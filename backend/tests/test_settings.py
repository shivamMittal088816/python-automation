import unittest

from pydantic import ValidationError

from app.config.settings import Settings


class SettingsTests(unittest.TestCase):
    def values(self, **overrides):
        values = {
            'DB_HOST': 'localhost',
            'DB_PORT': 3306,
            'DB_USER': 'user',
            'DB_PASSWORD': 'secret',
            'DB_NAME': 'students',
            'CORS_ORIGINS': 'https://app.example.com',
        }
        values.update(overrides)
        return values

    def test_credentialed_cors_rejects_wildcard_origin(self):
        with self.assertRaisesRegex(ValidationError, 'explicit frontend origins'):
            Settings(_env_file=None, **self.values(CORS_ORIGINS='*'))

    def test_cross_site_cookie_requires_https(self):
        with self.assertRaisesRegex(ValidationError, 'requires SESSION_COOKIE_SECURE=true'):
            Settings(_env_file=None, **self.values(
                SESSION_COOKIE_SAMESITE='none', SESSION_COOKIE_SECURE=False))

    def test_exact_origin_and_secure_cross_site_cookie_are_valid(self):
        configured = Settings(_env_file=None, **self.values(SESSION_COOKIE_SAMESITE='none'))
        self.assertEqual(configured.CORS_ORIGINS, 'https://app.example.com')
        self.assertEqual(configured.SESSION_COOKIE_SAMESITE, 'none')


if __name__ == '__main__':
    unittest.main()
