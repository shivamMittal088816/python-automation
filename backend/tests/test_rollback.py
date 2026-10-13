"""Rollback file upload and school verification API tests."""

import asyncio
from contextlib import contextmanager
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from openpyxl import Workbook, load_workbook

from app.main import create_app
from app.services import rollback as rollback_storage
from tests.test_file_workflow_api import asgi_request


class RollbackAPITests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = patch.object(rollback_storage.config, 'ROOT', Path(temporary.name))
        root.start()
        self.addCleanup(root.stop)
        self.app = create_app()
        self.dump_result = {
            'columns': ['user_id', 'admission_number', 'user_edu_school'],
            'rows': [['1', '0007', '914'], ['2', '0008', '914']],
        }

        @contextmanager
        def stream_dump(school_index):
            self.streamed_school_indexes.append(school_index)
            yield self.dump_result['columns'], iter(self.dump_result['rows'])

        self.streamed_school_indexes = []
        dump = patch(
            'app.routes.rollback.school_routes.stream_rollback_dump',
            side_effect=stream_dump,
        )
        self.stream_rollback_dump = dump.start()
        self.addCleanup(dump.stop)

    def upload(self, filename, data, content_type='application/octet-stream'):
        boundary = b'rollback-boundary'
        body = (
            b'--' + boundary + b'\r\n'
            + f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
            + f'Content-Type: {content_type}\r\n\r\n'.encode()
            + data + b'\r\n--' + boundary + b'--\r\n'
        )
        return asyncio.run(asgi_request(
            self.app, 'POST', '/api/v1/bulk-reg/rollback/files', body,
            [(b'content-type', b'multipart/form-data; boundary=rollback-boundary')],
        ))

    def test_upload_accepts_browser_csv_file(self):
        data = b'id,name\n' + b'1,Ada\n' * 25
        status, _, response = self.upload('rollback.csv', data, 'text/csv')

        self.assertEqual(status, 200)
        result = json.loads(response)
        self.assertEqual(result['name'], 'rollback.csv')
        self.assertEqual(result['row_count'], 25)
        self.assertEqual(result['columns'], ['id', 'name'])
        snapshots = list(rollback_storage.root_path().glob('*/*.bin'))
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].read_bytes(), data)

        status, _, response = asyncio.run(asgi_request(
            self.app, 'GET', '/api/v1/bulk-reg/rollback/files/preview?page=2',
        ))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(response)['page'], 2)

        status, _, response = asyncio.run(asgi_request(
            self.app, 'GET', '/api/v1/bulk-reg/rollback/workspace',
        ))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(response)['file']['name'], 'rollback.csv')

        status, _, response = asyncio.run(asgi_request(
            self.app, 'DELETE', '/api/v1/bulk-reg/rollback/files',
        ))
        self.assertEqual(status, 200)
        self.assertIsNone(json.loads(response)['file'])
        self.assertEqual(list(rollback_storage.root_path().glob('*/*.bin')), [])
        state = json.loads(next(rollback_storage.root_path().glob('*/state.json')).read_text())
        self.assertIsNone(state['input'])

    def test_sanity_check_enforces_server_owned_exact_header_policy(self):
        self.upload(
            'rollback.csv',
            b'USER_ID,FIRST NAME,unexpected\n1,Ada,value\n',
            'text/csv',
        )

        with patch(
            'app.routes.rollback.input_routes.preview_file',
            side_effect=AssertionError('sanity check reparsed the saved file'),
        ):
            status, _, response = asyncio.run(asgi_request(
                self.app, 'POST', '/api/v1/bulk-reg/rollback/files/sanity-check',
            ))

        self.assertEqual(status, 200)
        invalid = json.loads(response)
        self.assertFalse(invalid['valid'])
        self.assertEqual(invalid['missing_headers'], ['user_id'])
        self.assertEqual(invalid['unsupported_headers'], ['USER_ID', 'unexpected'])

        self.upload(
            'rollback.csv',
            b' user_id ,FIRST NAME,School Number\n1,Ada,914\n',
            'text/csv',
        )
        status, _, response = asyncio.run(asgi_request(
            self.app, 'POST', '/api/v1/bulk-reg/rollback/files/sanity-check',
        ))

        self.assertEqual(status, 200)
        valid = json.loads(response)
        self.assertTrue(valid['valid'])
        self.assertEqual(valid['missing_headers'], [])
        self.assertEqual(valid['unsupported_headers'], [])
        self.assertEqual(
            valid['message'],
            'Sanity check passed. All headers are allowed and user_id is present.',
        )

    def test_excel_upload_can_select_a_worksheet(self):
        workbook = Workbook()
        workbook.active.title = 'First'
        workbook.active.append(['name'])
        workbook.active.append(['Ada'])
        second = workbook.create_sheet('Second')
        second.append(['name'])
        second.append(['Grace'])
        source = BytesIO()
        workbook.save(source)

        status, _, _ = self.upload(
            'rollback.xlsx', source.getvalue(),
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertEqual(status, 200)
        status, _, response = asyncio.run(asgi_request(
            self.app, 'POST', '/api/v1/bulk-reg/rollback/files/sheet',
            json.dumps({'sheet': 'Second'}).encode(),
            [(b'content-type', b'application/json')],
        ))

        self.assertEqual(status, 200)
        result = json.loads(response)
        self.assertEqual(result['sheets'], ['First', 'Second'])
        self.assertEqual(result['sheet'], 'Second')
        self.assertEqual(result['rows'], [['Grace']])

    def test_legacy_json_dump_is_migrated_to_bin_on_read(self):
        workspace_id = rollback_storage.create_workspace()
        folder = rollback_storage.root_path() / workspace_id
        legacy = {
            'columns': ['user_id', 'admission_number'],
            'rows': [['1', '0007'], ['2', '0008']],
        }
        (folder / 'dump.json').write_text(json.dumps(legacy), encoding='utf-8')
        state = rollback_storage.load_state(workspace_id)
        state['school'] = {'school_index': '914', 'school_name': 'North School'}
        state['dump'] = {
            'file': 'dump.json', 'row_count': 2, 'columns': legacy['columns'],
        }
        rollback_storage.save_state(workspace_id, state)

        preview = rollback_storage.read_dump_page(workspace_id, 1, 20)

        self.assertEqual(preview['rows'], legacy['rows'])
        migrated = rollback_storage.load_state(workspace_id)
        self.assertTrue(migrated['dump']['file'].startswith('dump-'))
        self.assertTrue(migrated['dump']['file'].endswith('.bin'))
        self.assertFalse((folder / 'dump.json').exists())
        self.assertTrue((folder / migrated['dump']['file']).is_file())

    def test_dump_replacement_commits_manifest_before_deleting_previous_snapshot(self):
        workspace_id = rollback_storage.create_workspace()
        school = {'school_index': '914', 'school_name': 'North School'}
        rollback_storage.save_school_rows(
            workspace_id, school, ['user_id'], iter([['1']]),
        )
        before = rollback_storage.load_state(workspace_id)
        previous = rollback_storage.root_path() / workspace_id / before['dump']['file']

        with patch('app.services.rollback.dump_snapshots.save_state', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                rollback_storage.save_school_rows(
                    workspace_id, school, ['user_id'], iter([['2']]),
                )

        self.assertTrue(previous.is_file())
        persisted = json.loads(
            (rollback_storage.root_path() / workspace_id / 'state.json').read_text(encoding='utf-8')
        )
        self.assertEqual(persisted['dump']['file'], before['dump']['file'])

    @patch('app.routes.bulk_registration.school_routes.fetch_school')
    def test_school_number_returns_database_name(self, fetch_school):
        fetch_school.return_value = {'school_index': '914', 'school_name': 'North School'}

        status, _, response = asyncio.run(asgi_request(
            self.app, 'GET', '/api/v1/bulk-reg/schools/914',
        ))

        self.assertEqual(status, 200)
        self.assertEqual(json.loads(response), {
            'school_index': '914', 'school_name': 'North School',
        })
        fetch_school.assert_called_once_with('914')

    @patch('app.routes.rollback.school_routes.fetch_school')
    def test_rollback_school_is_restored_and_can_be_cleared(self, fetch_school):
        fetch_school.return_value = {'school_index': '914', 'school_name': 'North School'}
        payload = json.dumps({'school_index': '914'}).encode()

        status, _, response = asyncio.run(asgi_request(
            self.app, 'POST', '/api/v1/bulk-reg/rollback/school', payload,
            [(b'content-type', b'application/json')],
        ))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(response)['school']['school_name'], 'North School')
        self.assertEqual(self.streamed_school_indexes, ['914'])

        self.upload('rollback.csv', b'id,name\n1,Ada\n', 'text/csv')
        status, _, response = asyncio.run(asgi_request(
            self.app, 'GET', '/api/v1/bulk-reg/rollback/workspace',
        ))
        self.assertEqual(status, 200)
        restored = json.loads(response)
        self.assertEqual(restored['school'], {
            'school_index': '914', 'school_name': 'North School',
        })
        self.assertEqual(restored['file']['name'], 'rollback.csv')
        self.assertEqual(restored['dump']['row_count'], 2)
        self.assertEqual(restored['dump']['rows'][0], ['1', '0007', '914'])
        folder = next(rollback_storage.root_path().iterdir())
        dump_snapshots = list(folder.glob('dump-*.bin'))
        self.assertEqual(len(dump_snapshots), 1)
        self.assertIn(b'user_id,admission_number,user_edu_school', dump_snapshots[0].read_bytes())

        status, _, response = asyncio.run(asgi_request(
            self.app, 'DELETE', '/api/v1/bulk-reg/rollback/school',
        ))
        self.assertEqual(status, 200)
        self.assertIsNone(json.loads(response)['school'])

        status, _, response = asyncio.run(asgi_request(
            self.app, 'GET', '/api/v1/bulk-reg/rollback/workspace',
        ))
        restored = json.loads(response)
        self.assertIsNone(restored['school'])
        self.assertIsNone(restored['dump'])
        self.assertEqual(restored['file']['name'], 'rollback.csv')
        self.assertEqual(list(folder.glob('dump-*.bin')), [])

    @patch('app.routes.rollback.school_routes.fetch_school')
    def test_dump_preview_is_paginated_for_verified_school(self, fetch_school):
        fetch_school.return_value = {'school_index': '399', 'school_name': 'Example School'}
        self.dump_result = {
            'columns': ['user_id', 'user_edu_school'],
            'rows': [['=2+2' if index == 0 else str(index), '399'] for index in range(25)],
        }
        payload = json.dumps({'school_index': '399'}).encode()

        status, _, response = asyncio.run(asgi_request(
            self.app, 'POST', '/api/v1/bulk-reg/rollback/school', payload,
            [(b'content-type', b'application/json')],
        ))
        result = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(result['dump']['row_count'], 25)
        self.assertEqual(len(result['dump']['rows']), 20)

        status, _, response = asyncio.run(asgi_request(
            self.app, 'GET', '/api/v1/bulk-reg/rollback/dump/preview?page=2',
        ))
        second = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(second['page'], 2)
        self.assertEqual(len(second['rows']), 5)
        self.assertEqual(second['rows'][0], ['20', '399'])
        self.assertEqual(self.streamed_school_indexes, ['399'])

        status, headers, csv_data = asyncio.run(asgi_request(
            self.app, 'GET', '/api/v1/bulk-reg/rollback/dump/download?file_format=csv',
        ))
        self.assertEqual(status, 200)
        self.assertIn(b'rollback-dump-399.csv', headers[b'content-disposition'])
        self.assertTrue(csv_data.startswith(b'\xef\xbb\xbfuser_id,user_edu_school\n'))
        self.assertIn(b"'=2+2,399\n", csv_data)
        self.assertIn(b'24,399\n', csv_data)

        status, headers, xlsx_data = asyncio.run(asgi_request(
            self.app, 'GET', '/api/v1/bulk-reg/rollback/dump/download?file_format=xlsx',
        ))
        self.assertEqual(status, 200)
        self.assertIn(b'rollback-dump-399.xlsx', headers[b'content-disposition'])
        workbook = load_workbook(BytesIO(xlsx_data), read_only=True, data_only=True)
        sheet = workbook['Rollback dump']
        self.assertEqual([cell.value for cell in next(sheet.iter_rows())],
                         ['user_id', 'user_edu_school'])
        self.assertEqual(sheet['A2'].value, '=2+2')
        self.assertEqual(sheet['A26'].value, '24')


if __name__ == '__main__':
    unittest.main()
