"""Workspace concurrency and committed-output regressions, using isolated files."""
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import asyncio
import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request, Response, UploadFile
from openpyxl import Workbook

from app.routes.bulk_registration import conversion_routes, file_routes, workspace_routes
from app.routes.bulk_registration.models import StoredFileInput
from app.routes.bulk_registration.workspace_access import BULK_COOKIE
from app.services import bulk_registration_storage as storage
from app.main import create_app
from tests.test_file_workflow_api import asgi_request


class BulkWorkspaceTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = patch.object(storage, 'ROOT', Path(temporary.name))
        root.start()
        self.addCleanup(root.stop)
        self.workspace_id = storage.create_workspace()

    def request(self):
        return Request({'type': 'http', 'headers': [
            (b'cookie', f'{BULK_COOKIE}={self.workspace_id}'.encode()),
        ]})

    def test_stale_upload_after_reset_cannot_replace_the_cookie(self):
        app = create_app()
        old_cookie = f'{BULK_COOKIE}={self.workspace_id}'.encode()
        status, headers, body = asyncio.run(asgi_request(
            app, 'DELETE', '/api/v1/bulk-reg/workspace', headers=[
                (b'cookie', old_cookie), (b'x-workspace-revision', b'0'),
            ],
        ))
        self.assertEqual(status, 200)
        reset = json.loads(body)
        new_cookie = headers[b'set-cookie'].split(b';', 1)[0]
        folders = set(storage.ROOT.iterdir())
        multipart = (
            b'--review-boundary\r\n'
            b'Content-Disposition: form-data; name="file"; filename="students.csv"\r\n'
            b'Content-Type: text/csv\r\n\r\n'
            b'FIRST NAME\nAda\n\r\n--review-boundary--\r\n'
        )

        def upload(cookie):
            return asyncio.run(asgi_request(app, 'POST', '/api/v1/bulk-reg/files', multipart, [
                (b'cookie', cookie), (b'x-workspace-revision', b'0'),
                (b'content-type', b'multipart/form-data; boundary=review-boundary'),
            ]))

        for cookie in (old_cookie, b'', f'{BULK_COOKIE}=invalid'.encode()):
            with self.subTest(cookie=cookie):
                status, headers, _ = upload(cookie)
                self.assertEqual(status, 409)
                self.assertNotIn(b'set-cookie', headers)
                self.assertEqual(set(storage.ROOT.iterdir()), folders)

        status, _, body = asyncio.run(asgi_request(
            app, 'GET', '/api/v1/bulk-reg/workspace', headers=[(b'cookie', new_cookie)],
        ))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), reset)
        status, headers, body = upload(new_cookie)
        self.assertEqual(status, 200)
        self.assertNotIn(b'set-cookie', headers)
        self.assertEqual(json.loads(body)['workspace_id'], reset['workspace_id'])

    def test_workspace_initialization_still_recovers_a_missing_workspace(self):
        storage.delete_workspace(self.workspace_id)
        response = Response()
        result = workspace_routes.initialize_workspace(self.request(), response)
        self.assertIn('set-cookie', response.headers)
        self.assertEqual(result['revision'], 0)
        self.assertIsNone(result['file'])

    def test_delayed_refresh_after_reset_cannot_replace_the_cookie(self):
        app = create_app()
        old_cookie = f'{BULK_COOKIE}={self.workspace_id}'.encode()
        status, headers, body = asyncio.run(asgi_request(
            app, 'DELETE', '/api/v1/bulk-reg/workspace', headers=[
                (b'cookie', old_cookie), (b'x-workspace-revision', b'0'),
            ],
        ))
        self.assertEqual(status, 200)
        reset = json.loads(body)
        new_cookie = headers[b'set-cookie'].split(b';', 1)[0]
        folders = set(storage.ROOT.iterdir())
        for cookie in (old_cookie, b'', f'{BULK_COOKIE}=invalid'.encode()):
            with self.subTest(cookie=cookie):
                status, headers, _ = asyncio.run(asgi_request(
                    app, 'GET', '/api/v1/bulk-reg/workspace', headers=[(b'cookie', cookie)],
                ))
                self.assertEqual(status, 409)
                self.assertNotIn(b'set-cookie', headers)
                self.assertEqual(set(storage.ROOT.iterdir()), folders)
        # Initialization is idempotent when another tab has already recovered.
        status, headers, body = asyncio.run(asgi_request(
            app, 'POST', '/api/v1/bulk-reg/workspace', headers=[(b'cookie', new_cookie)],
        ))
        self.assertEqual(status, 200)
        self.assertNotIn(b'set-cookie', headers)
        self.assertEqual(json.loads(body), reset)

    def test_simultaneous_mutations_reject_the_stale_revision(self):
        first_loaded, second_started, second_loaded = Event(), Event(), Event()
        original = workspace_routes.workspace_for

        def controlled_read(request, response):
            result = original(request, response)
            if not first_loaded.is_set():
                first_loaded.set()
                self.assertTrue(second_started.wait(5))
                # Without the operation lock, the second request reads revision 0
                # here. With it, that read waits until the first request commits.
                second_loaded.wait(0.5)
            else:
                second_loaded.set()
            return result

        def clear(second=False):
            if second:
                second_started.set()
            try:
                result = workspace_routes.clear_file(self.request(), Response(), 0)
                return 200, result['revision']
            except HTTPException as error:
                return error.status_code, None

        with patch.object(workspace_routes, 'workspace_for', controlled_read), ThreadPoolExecutor(2) as pool:
            first = pool.submit(clear)
            self.assertTrue(first_loaded.wait(5))
            second = pool.submit(clear, True)
            self.assertEqual(first.result(timeout=5), (200, 1))
            self.assertEqual(second.result(timeout=5), (409, None))
        self.assertEqual(storage.load_workspace(self.workspace_id)['revision'], 1)

    def test_sheet_change_and_failed_conversion_preserve_output_and_passwords(self):
        workbook = Workbook()
        workbook.active.title = 'Students'
        workbook.active.append(['FIRST NAME'])
        workbook.active.append(['Ada'])
        workbook.create_sheet('Empty')
        source = BytesIO()
        workbook.save(source)
        workbook.close()
        file_routes.upload_workspace_file(
            self.request(), Response(), 0,
            UploadFile(filename='students.xlsx', file=BytesIO(source.getvalue())), None,
        )

        def convert(revision, format='preview'):
            return conversion_routes.convert_workspace_file(
                self.request(), Response(), revision, '914', format,
                file=None, path=None, sheet=None, page=1,
            )

        with patch.object(conversion_routes, 'get_school', return_value={
            'school_index': '914', 'school_name': 'Test School',
        }), patch.object(conversion_routes, 'fetch_sections', return_value=[]):
            preview = convert(1)
            before = convert(2, 'csv').body
            changed = file_routes.load_stored_file(
                StoredFileInput(sheet='Empty'), self.request(), Response(), 2,
            )
            self.assertEqual(changed['output'], preview['output'])
            self.assertEqual(changed['file']['sheet'], 'Empty')
            with self.assertRaises(HTTPException) as failure:
                convert(3)
            self.assertEqual(failure.exception.status_code, 400)
            self.assertEqual(convert(3, 'csv').body, before)
            state = storage.load_workspace(self.workspace_id)
            self.assertEqual(state['revision'], 3)
            self.assertEqual(state['output'], preview['output'])
            storage.read_snapshot(self.workspace_id, state['outputs']['authoritative'])
