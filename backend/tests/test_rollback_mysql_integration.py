"""Opt-in integration coverage for rollback SQL against real MySQL types.

Set ROLLBACK_MYSQL_TEST_URL to a disposable MySQL database URL to run this test.
The test creates a connection-local TEMPORARY users table, so the real users
table is never read or modified.
"""

from datetime import datetime
import os
import unittest

from sqlalchemy import create_engine, text

from app.repositories.rollback_update_repository import FALLBACK_UPDATE_QUERY


MYSQL_TEST_URL = os.getenv('ROLLBACK_MYSQL_TEST_URL')


@unittest.skipUnless(
    MYSQL_TEST_URL,
    'Set ROLLBACK_MYSQL_TEST_URL to run MySQL rollback integration tests.',
)
class RollbackMySQLIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(MYSQL_TEST_URL, pool_pre_ping=True)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_fallback_update_uses_real_mysql_column_types(self):
        connection = self.engine.connect().execution_options(
            isolation_level='AUTOCOMMIT'
        )
        try:
            # A MySQL temporary table shadows any permanent table with the same
            # name for this connection only. The production users table cannot
            # be reached by the update below.
            connection.execute(text('''
                CREATE TEMPORARY TABLE users (
                    user_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    user_type ENUM('0', '1') NOT NULL DEFAULT '0',
                    user_edu_school VARCHAR(256) NULL,
                    user_edu_class VARCHAR(256) NULL,
                    user_package INT UNSIGNED NULL,
                    user_activated ENUM('0', '1') NOT NULL DEFAULT '0',
                    user_subscribed ENUM('0', '1') NOT NULL DEFAULT '0',
                    user_subscription_date DATETIME NULL
                )
            '''))
            connection.execute(text('''
                INSERT INTO users (
                    user_id, user_type, user_edu_school, user_edu_class,
                    user_package, user_activated, user_subscribed,
                    user_subscription_date
                ) VALUES
                    (1, '0', '399', '5', 14, '1', '1', '2026-04-01 00:00:00'),
                    (2, '0', '399', '6', 14, '1', '1', '2026-04-01 00:00:00'),
                    (3, '0', '400', '7', 14, '1', '1', '2026-04-01 00:00:00'),
                    (4, '1', '399', '8', 14, '1', '1', '2026-04-01 00:00:00'),
                    (5, '0', '399', '9', 12, '1', '1', '2026-04-01 00:00:00')
            '''))

            result = connection.execute(FALLBACK_UPDATE_QUERY, {
                'school_index': '399',
                'supplied_ids': [2],
            })

            self.assertEqual(result.rowcount, 1)
            rows = {
                row['user_id']: row
                for row in connection.execute(text('''
                    SELECT user_id, user_type, user_edu_school, user_edu_class,
                           user_package, user_activated, user_subscribed,
                           user_subscription_date
                    FROM users
                    ORDER BY user_id
                ''')).mappings()
            }

            changed = rows[1]
            self.assertEqual(changed['user_edu_class'], '4')
            self.assertEqual(changed['user_package'], 12)
            self.assertEqual(changed['user_activated'], '0')
            self.assertEqual(changed['user_subscribed'], '0')
            self.assertEqual(
                changed['user_subscription_date'],
                datetime(2025, 4, 1, 0, 0, 0),
            )

            # Sheet user, other school, non-student type, and package 12 are
            # all outside the write scope and must remain unchanged.
            self.assertEqual(rows[2]['user_package'], 14)
            self.assertEqual(rows[2]['user_edu_class'], '6')
            self.assertEqual(rows[3]['user_package'], 14)
            self.assertEqual(rows[4]['user_package'], 14)
            self.assertEqual(rows[5]['user_package'], 12)
            self.assertEqual(rows[5]['user_edu_class'], '9')
        finally:
            connection.execute(text('DROP TEMPORARY TABLE IF EXISTS users'))
            connection.close()


if __name__ == '__main__':
    unittest.main()
