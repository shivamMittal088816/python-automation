from datetime import timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sqlalchemy import select

from app.api import file_workflow_state
from app.auth.models import User, AuthSession, AuthRateLimit
from app.auth.services.cookies import cookie_name
from app.auth.services.tokens import token_hash
from app.common.time import now
from app.auth.services.passwords import verify_password
from app.config.settings import settings
from app.main import create_app
from tests.invitation_fixture import invitation_database, override_database, InvitationTestClient

PASSWORD = 'my memorable school passphrase!'


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.engine, self.factory = invitation_database(root)
        self.addCleanup(self.engine.dispose)
        for model in (User, AuthSession, AuthRateLimit):
            model.__table__.create(self.engine, checkfirst=True)
        for target, attribute, value in ((settings, 'AUTH_REQUIRED', True),
                                          (settings, 'SESSION_COOKIE_SECURE', False),
                                          (settings, 'CORS_ORIGINS', 'http://127.0.0.1:5174'),
                                          (file_workflow_state, 'ROOT', root / 'mapping')):
            patcher = patch.object(target, attribute, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.app = create_app()
        override_database(self.app, self.factory)
        self.client = InvitationTestClient(self.app)
        self.client.headers['origin'] = 'http://127.0.0.1:5174'

    def register(self, **changes):
        return self.client.post('/api/v1/auth/register', json={
            'name': 'Alex Morgan', 'email': 'alex@example.com', 'password': PASSWORD, **changes})

    def test_registration_hashes_password_and_cookie_authenticates_protected_api(self):
        self.assertEqual(self.client.post('/api/v1/mapping/session', json={}).status_code, 401)
        response = self.register()
        self.assertEqual(response.status_code, 201, response.text)
        cookie = response.headers['set-cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=lax', cookie)
        self.assertIn('Path=/', cookie)
        self.assertNotIn('password', response.text)
        token = self.client.cookies[cookie_name()]
        with self.factory() as db:
            user = db.scalar(select(User))
            self.assertNotEqual(user.password_hash, PASSWORD)
            self.assertTrue(user.password_hash.startswith('scrypt$131072$8$1$'))
            self.assertTrue(verify_password(PASSWORD, user.password_hash))
            session = db.get(AuthSession, token_hash(token))
            self.assertEqual(session.user_id, user.id)
            self.assertNotEqual(session.token_hash, token)
        self.assertEqual(self.client.get('/api/v1/auth/me').json()['user']['email'], 'alex@example.com')
        self.assertEqual(self.client.post('/api/v1/mapping/session', json={}).status_code, 200)

    def test_logout_revokes_replayed_cookie_and_clears_workflow_access(self):
        self.register()
        self.client.post('/api/v1/mapping/session', json={})
        token = self.client.cookies[cookie_name()]
        self.assertEqual(self.client.post('/api/v1/auth/logout').status_code, 204)
        self.assertEqual(self.client.cookies, {})
        self.client.cookies[cookie_name()] = token
        self.assertIsNone(self.client.get('/api/v1/auth/me').json()['user'])
        self.assertEqual(self.client.post('/api/v1/mapping/session', json={}).status_code, 401)

    def test_login_normalizes_email_rotates_session_and_rejects_wrong_credentials(self):
        self.register(email=' ALEX@EXAMPLE.COM ')
        original = self.client.cookies[cookie_name()]
        wrong = self.client.post('/api/v1/auth/login', json={'email': 'alex@example.com', 'password': 'wrong'})
        missing = self.client.post('/api/v1/auth/login', json={'email': 'missing@example.com', 'password': 'wrong'})
        self.assertEqual((wrong.status_code, missing.status_code), (401, 401))
        self.assertEqual(wrong.json()['detail'], missing.json()['detail'])
        response = self.client.post('/api/v1/auth/login', json={'email': 'Alex@Example.com', 'password': PASSWORD})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotEqual(self.client.cookies[cookie_name()], original)
        with self.factory() as db:
            self.assertIsNotNone(db.get(AuthSession, token_hash(original)).revoked_at)

    def test_expired_session_and_disabled_account_cannot_access_apis(self):
        self.register()
        with self.factory() as db:
            session = db.scalar(select(AuthSession))
            session.expires_at = now() - timedelta(seconds=1)
            db.commit()
        self.assertEqual(self.client.post('/api/v1/mapping/session', json={}).status_code, 401)
        self.client.post('/api/v1/auth/login', json={'email': 'alex@example.com', 'password': PASSWORD})
        with self.factory() as db:
            user = db.scalar(select(User))
            user.is_active = False
            db.commit()
        self.assertEqual(self.client.post('/api/v1/mapping/session', json={}).status_code, 401)

    def test_duplicate_email_validation_csrf_and_login_rate_limit(self):
        self.assertEqual(self.register(password='short').status_code, 422)
        self.assertNotIn('secretXYZ', self.register(password='secretXYZ').text)
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.register(email='ALEX@example.com').status_code, 409)
        cross_site = self.client.post('/api/v1/auth/logout', headers={'origin': 'https://untrusted.example'})
        self.assertEqual(cross_site.status_code, 403)
        self.assertIsNotNone(self.client.get('/api/v1/auth/me').json()['user'])
        with self.factory() as db:
            db.add(AuthRateLimit(key=token_hash('login:email:alex@example.com'), attempts=10, window_started_at=now()))
            db.commit()
        limited = self.client.post('/api/v1/auth/login', json={'email': 'alex@example.com', 'password': PASSWORD})
        self.assertEqual(limited.status_code, 429)

    def test_account_change_clears_previous_workspace_cookies_and_secure_cookie_flags(self):
        self.register()
        self.client.post('/api/v1/mapping/session', json={})
        self.assertEqual(self.register(name='Jamie', email='jamie@example.com').status_code, 201)
        self.assertNotIn('workspace-session', self.client.cookies)
        self.assertNotIn('student_mapping_session', self.client.cookies)
        with patch.object(settings, 'SESSION_COOKIE_SECURE', True):
            response = self.client.post('/api/v1/auth/login', json={'email': 'jamie@example.com', 'password': PASSWORD})
            self.assertEqual(response.status_code, 200)
            self.assertIn('__Host-auth-session=', response.headers['set-cookie'])
            self.assertIn('Secure', response.headers['set-cookie'])
