import asyncio
from tests import test_file_workflow_api as workflows
from app.config.settings import settings
asgi_request = workflows.asgi_request


class CookieSessionTests(workflows.FileWorkflowAPITests):
    def test_cookie_flags_and_no_secret_in_response(self):
        status, headers, body = asyncio.run(asgi_request(
            self.app, 'POST', '/api/v1/mapping/session', b'{}',
            [(b'content-type', b'application/json')]))
        self.assertEqual(status, 200)
        cookie = headers[b'set-cookie'].decode()
        for flag in ('HttpOnly', 'Secure', 'SameSite=lax', 'Path=/', 'Max-Age=259200'):
            self.assertIn(flag, cookie)
        secret = self.app.state.test_cookie.split(b'=', 1)[1]
        self.assertNotIn(secret, body)
        self.assertNotIn(b'"session_id"', body)

    def test_requires_cookie_and_rejects_old_url(self):
        self.json('GET', self.endpoint(), expected=401, headers=[(b'cookie', b'')])
        self.json('GET', self.endpoint(), expected=401,
                  headers=[(b'cookie', b'__Host-student-mapping-session=invalid')])
        self.json('GET', '/mapping/sessions/' + self.id, expected=404)
        self.json('GET', self.endpoint())

    def test_rejects_foreign_origin_mutation(self):
        self.json('POST', self.endpoint('/admission-mapping/run'), {}, expected=403,
                  headers=[(b'origin', b'https://untrusted.example')])

    def test_allows_configured_frontend_origin_across_origins(self):
        origin = next(value.strip() for value in settings.CORS_ORIGINS.split(',') if value.strip())
        status, _, _ = asyncio.run(asgi_request(
            self.app, 'POST', '/api/v1/mapping/session', b'{}',
            [(b'content-type', b'application/json'),
             (b'origin', origin.encode()),
             (b'sec-fetch-site', b'cross-site')]))
        self.assertEqual(status, 200)

    def test_api_does_not_accept_session_id_parameters(self):
        for path, methods in self.app.openapi()['paths'].items():
            self.assertNotIn('{session_id}', path)
            for operation in methods.values():
                self.assertFalse(any(p['name'] == 'session_id' for p in operation.get('parameters', [])))
