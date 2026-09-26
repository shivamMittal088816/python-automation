"""Status, CORS, cache and request-ID contracts for actual ASGI responses."""
import asyncio
import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.config.settings import settings
from app.main import create_app
from app.services.bulk_registration import SchoolNotFoundError
from tests.test_file_workflow_api import asgi_request


class RequestDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.origin = next(value.strip() for value in settings.CORS_ORIGINS.split(',') if value.strip())

    def request(self, path, request_id='audit-request-1', method='GET', body=b''):
        return asyncio.run(asgi_request(self.app, method, path, body, [
            (b'origin', self.origin.encode()), (b'x-request-id', request_id.encode()),
            (b'content-type', b'application/json'),
        ]))

    def assert_diagnostics(self, status, headers, expected):
        self.assertEqual(status, expected)
        self.assertEqual(headers[b'x-request-id'], b'audit-request-1')
        self.assertTrue(headers[b'server-timing'].startswith(b'app;dur='))
        self.assertEqual(headers[b'cache-control'], b'no-store')
        self.assertEqual(headers[b'access-control-allow-origin'].decode(), self.origin)
        self.assertIn(b'X-Request-ID', headers[b'access-control-expose-headers'])

    def test_status_matrix_and_log_severity(self):
        for code in (200, 400, 401, 403, 404, 409, 413, 422, 500, 503):
            path = f'/api/v1/bulk-reg/diagnostic-{code}'
            async def endpoint(status=code):
                if status != 200:
                    raise HTTPException(status, 'Expected failure')
                return {'ok': True}
            self.app.add_api_route(path, endpoint, methods=['GET'])
            with self.subTest(status=code), self.assertLogs('uvicorn.error', level='INFO') as logs:
                status, headers, _ = self.request(path)
            self.assert_diagnostics(status, headers, code)
            level = 'ERROR' if code >= 500 else 'WARNING' if code >= 400 else 'INFO'
            self.assertTrue(any(line.startswith(level + ':') and f'status={code}' in line
                                and 'request_id=audit-request-1' in line for line in logs.output))

    def test_unhandled_error_is_traceable_and_browser_readable(self):
        @self.app.get('/api/v1/bulk-reg/crash')
        async def crash():
            raise RuntimeError('private-internal-detail')
        with self.assertLogs('uvicorn.error', level='ERROR') as logs:
            status, headers, body = self.request('/api/v1/bulk-reg/crash')
        self.assert_diagnostics(status, headers, 500)
        self.assertNotIn(b'private-internal-detail', body)
        self.assertIn('unexpected server error', json.loads(body)['detail'])
        self.assertTrue(any('Unhandled API error' in line and 'request_id=audit-request-1' in line for line in logs.output))
        self.assertTrue(any('completed status=500' in line for line in logs.output))

    def test_untrusted_request_ids_are_replaced(self):
        for supplied in ('x' * 65, 'bad\nlog-entry', 'bad id'):
            with self.subTest(value=supplied):
                status, headers, _ = self.request('/api/v1/mapping/health', supplied)
                self.assertEqual(status, 200)
                self.assertRegex(headers[b'x-request-id'].decode(), r'^[a-f0-9-]{36}$')

    def test_real_bulk_school_failures_have_distinct_statuses(self):
        for exception, expected in (
            (ValueError('Enter a numeric school index.'), 400),
            (SchoolNotFoundError('No school found.'), 404),
            (SQLAlchemyError('private SQL details'), 503),
        ):
            with self.subTest(status=expected), patch('app.routes.bulk_registration.fetch_school', side_effect=exception):
                status, headers, body = self.request('/api/v1/bulk-reg/schools/914')
            self.assert_diagnostics(status, headers, expected)
            self.assertNotIn(b'private SQL details', body)

    def test_framework_validation_and_missing_session_are_traced(self):
        for method, path, body, expected in (
            ('GET', '/api/v1/mapping/session', b'', 401),
            ('POST', '/api/v1/bulk-reg/files/path', b'{}', 422),
            ('GET', '/api/v1/bulk-reg/nonexistent-route', b'', 404),
        ):
            with self.subTest(path=path):
                status, headers, _ = self.request(path, method=method, body=body)
                self.assert_diagnostics(status, headers, expected)
