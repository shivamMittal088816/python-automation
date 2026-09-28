"""Email verification checks and saved-output API coverage."""
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from fastapi import HTTPException, Response
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.email_repository import fetch_existing_emails
from app.routes.bulk_registration import conversion_routes
from app.services.bulk_registration import fill_blank_emails, verify_output_emails
from tests import test_bulk_registration_workspace as workspace_tests


class EmailVerificationTests(unittest.TestCase):
    def test_three_stages_report_blanks_and_compare_case_insensitively(self):
        frame = pd.DataFrame({'EMAIL': [' Ada@school.com ', 'ada@school.com',
                                      'bob@school.com', '', ' ', None]})
        result = verify_output_emails(frame, {'BOB@school.com'})
        self.assertFalse(result['passed'])
        self.assertEqual(result['checked_emails'], 6)
        self.assertEqual(len(result['stages']), 3)
        self.assertEqual(result['stages'][2]['issues'], [4, 5, 6])
        self.assertEqual(result['stages'][2]['failed_records']['rows'], [[4, ''], [5, ' '], [6, '']])
        self.assertEqual(result['stages'][0]['issues'], ['ada@school.com'])
        self.assertEqual(result['stages'][1]['issues'], ['bob@school.com'])
        self.assertEqual(result['stages'][0]['failed_records']['rows'], [
            [1, ' Ada@school.com '], [2, 'ada@school.com'],
        ])
        self.assertEqual(result['stages'][1]['failed_records']['rows'], [[3, 'bob@school.com']])
        self.assertTrue(verify_output_emails(pd.DataFrame({'EMAIL': ['new@school.com']}), set())['passed'])
        self.assertFalse(verify_output_emails(pd.DataFrame({'EMAIL': ['', None]}), set())['passed'])

    def test_database_lookup_uses_parameterized_in_and_skips_empty_input(self):
        connection = MagicMock()
        connection.execute.return_value.all.return_value = [('ada@school.com',)]
        with patch('app.config.database.engine.connect') as connect:
            connect.return_value.__enter__.return_value = connection
            self.assertEqual(fetch_existing_emails(['']), set())
            connect.assert_not_called()
            result = fetch_existing_emails([' ADA@school.com ', 'ada@school.com', "o'hara@school.com"])
        self.assertEqual(result, {'ada@school.com'})
        query, parameters = connection.execute.call_args.args
        self.assertIn('WHERE LOWER(TRIM(u.user_email)) IN', str(query))
        self.assertNotIn("o'hara", str(query))
        self.assertEqual(parameters, {'emails': ['ada@school.com', "o'hara@school.com"]})

    def test_database_lookup_normalizes_stored_addresses_before_filtering(self):
        engine = create_engine('sqlite://')
        self.addCleanup(engine.dispose)
        stored = [' ADA@school.com ', 'Bob@school.com', " O'Hara@school.com "]
        with engine.begin() as connection:
            connection.execute(text('CREATE TABLE users (user_email TEXT COLLATE BINARY)'))
            connection.execute(text('INSERT INTO users (user_email) VALUES (:email)'),
                               [{'email': email} for email in [*stored, 'unrelated@school.com', None]])
        frame = pd.DataFrame({'EMAIL': ['ada@school.com', ' BOB@school.com ',
                                       "o'hara@school.com", 'new@school.com']})
        with patch('app.config.database.engine', engine):
            existing = fetch_existing_emails(frame['EMAIL'])
        self.assertEqual(existing, set(stored))
        result = verify_output_emails(frame, existing)
        self.assertFalse(result['passed'])
        self.assertEqual(result['stages'][1]['issues'],
                         ['ada@school.com', 'bob@school.com', "o'hara@school.com"])
        self.assertEqual(result['stages'][1]['failed_records']['row_count'], 3)

    def test_non_ascii_school_preserves_supplied_emails(self):
        frame = pd.DataFrame({'EMAIL': [' Supplied@example.org '], 'user_name': ['ada001']})
        original = frame.copy()
        fill_blank_emails(frame, 'विद्यालय')
        pd.testing.assert_frame_equal(frame, original)

    def test_non_ascii_school_does_not_block_rows_without_usable_usernames(self):
        frame = pd.DataFrame({'EMAIL': ['', ' '], 'user_name': ['', '!!!']})
        original = frame.copy()
        fill_blank_emails(frame, 'विद्यालय')
        pd.testing.assert_frame_equal(frame, original)

    def test_non_ascii_school_still_rejects_required_email_generation(self):
        frame = pd.DataFrame({'EMAIL': ['supplied@example.org', ''],
                              'user_name': ['ada001', 'bob001']})
        original = frame.copy()
        with self.assertRaisesRegex(ValueError, 'school name cannot be used'):
            fill_blank_emails(frame, 'विद्यालय')
        pd.testing.assert_frame_equal(frame, original)


class EmailVerificationRouteTests(unittest.TestCase):
    setUp = workspace_tests.BulkWorkspaceTests.setUp
    request = workspace_tests.BulkWorkspaceTests.request

    def test_missing_preview_is_rejected_without_database_lookup(self):
        with patch.object(conversion_routes, 'fetch_existing_emails') as fetch:
            with self.assertRaises(HTTPException) as error:
                conversion_routes.verify_output_email_addresses(self.request(), Response())
        self.assertEqual(error.exception.status_code, 409)
        fetch.assert_not_called()

    def test_checks_full_saved_output_and_reports_database_failure(self):
        from app.services import bulk_registration_storage as storage
        frame = pd.DataFrame({'EMAIL': ['ada@school.com'] * 21 + ['existing@school.com']})
        state = storage.load_workspace(self.workspace_id)
        state['output'] = {'row_count': 22, 'rows': [['ada@school.com']] * 20}
        storage.save_workspace(self.workspace_id, state, {
            '_output_authoritative': ({'name': 'output.csv'}, frame.to_csv(index=False).encode()),
        })
        with patch.object(conversion_routes, 'fetch_existing_emails', return_value={'existing@school.com'}) as fetch:
            result = conversion_routes.verify_output_email_addresses(self.request(), Response())
        self.assertEqual(len(fetch.call_args.args[0]), 22)
        self.assertEqual(result['checked_emails'], 22)
        self.assertEqual(result['stages'][0]['issues'], ['ada@school.com'])
        self.assertEqual(result['stages'][1]['issues'], ['existing@school.com'])
        self.assertEqual(result['stages'][0]['failed_records']['row_count'], 21)
        self.assertEqual(result['stages'][1]['failed_records']['rows'], [[22, 'existing@school.com']])
        with patch.object(conversion_routes, 'fetch_existing_emails', side_effect=SQLAlchemyError('offline')):
            with self.assertRaises(HTTPException) as error:
                conversion_routes.verify_output_email_addresses(self.request(), Response())
        self.assertEqual(error.exception.status_code, 503)
