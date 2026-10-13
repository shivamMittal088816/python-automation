"""Rollback file upload and school verification API tests."""

import asyncio
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from openpyxl import Workbook

from app.main import create_app
from app.services import rollback_storage
from tests.test_file_workflow_api import asgi_request


class RollbackAPITests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = patch.object(rollback_storage, 'ROOT', Path(temporary.name))
        root.start()
        self.addCleanup(root.stop)
        self.app = create_app()

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
        snapshots = list(rollback_storage.ROOT.glob('*/*.bin'))
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
        self.assertEqual(list(rollback_storage.ROOT.glob('*/*.bin')), [])
        state = json.loads(next(rollback_storage.ROOT.glob('*/state.json')).read_text())
        self.assertIsNone(state['input'])

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

    @patch('app.routes.bulk_registration.school_routes.fetch_school')
    def test_rollback_school_is_restored_and_can_be_cleared(self, fetch_school):
        fetch_school.return_value = {'school_index': '914', 'school_name': 'North School'}
        payload = json.dumps({'school_index': '914'}).encode()

        status, _, response = asyncio.run(asgi_request(
            self.app, 'POST', '/api/v1/bulk-reg/rollback/school', payload,
            [(b'content-type', b'application/json')],
        ))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(response)['school']['school_name'], 'North School')

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
        self.assertEqual(restored['file']['name'], 'rollback.csv')


if __name__ == '__main__':
    unittest.main()
