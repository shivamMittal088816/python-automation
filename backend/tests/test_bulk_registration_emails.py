"""Email verification checks and saved-output API coverage."""
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from fastapi import HTTPException, Response
from sqlalchemy import create_engine, text

from app.repositories.email_repository import fetch_existing_emails
from app.routes.bulk_registration import conversion_routes
from app.services.bulk_registration import (
    fill_blank_emails, refresh_generated_emails, verify_output_emails,
)
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

    def test_refreshes_only_email_positions_generated_from_blank_input(self):
        frame = pd.DataFrame({
            'EMAIL': ['old001@testschool.com', 'supplied@example.org'],
            'user_name': ['new002', 'new003'],
        })

        refresh_generated_emails(frame, 'Test School', [0])

        self.assertEqual(frame['EMAIL'].tolist(), [
            'new002@testschool.com', 'supplied@example.org',
        ])


class EmailVerificationRouteTests(unittest.TestCase):
    setUp = workspace_tests.BulkWorkspaceTests.setUp
    request = workspace_tests.BulkWorkspaceTests.request

    def test_missing_preview_is_rejected_without_database_lookup(self):
        with self.assertRaises(HTTPException) as error:
            conversion_routes.verify_bulk_registration_output(self.request(), Response(), 0)
        self.assertEqual(error.exception.status_code, 409)

    def test_checks_full_saved_output_for_blank_and_duplicate_values(self):
        from app.services import bulk_registration_storage as storage
        frame = pd.DataFrame({
            'FIRST NAME': ['Ada'] * 21 + ['Blank'],
            'LAST NAME': [''] * 22,
            'FULL NAME': ['Ada Student'] * 21 + ['Blank Student'],
            'Section': ['A'] * 22,
            'Class Number': ['Class I'] * 22,
            'CLASS': ['1'] * 22,
            'GENDER': ['Female'] * 22,
            'Gender Number': ['2'] * 22,
            'section_index': ['1'] * 22,
            'user_name': ['ada001'] * 21 + [''],
            'EMAIL': ['ada@school.com'] * 21 + ['existing@school.com'],
            'admission_number': [str(index) for index in range(22)],
        })
        state = storage.load_workspace(self.workspace_id)
        state['output'] = {'row_count': 22, 'rows': [['ada@school.com']] * 20}
        storage.save_workspace(self.workspace_id, state, {
            '_output_authoritative': ({'name': 'output.csv'}, frame.to_csv(index=False).encode()),
        })
        with (
            patch.object(conversion_routes, 'fetch_existing_usernames', return_value=set()),
            patch.object(conversion_routes, 'fetch_existing_emails', return_value=set()),
            patch.object(conversion_routes, 'fetch_available_usernames',
                         side_effect=lambda names: [f'{name.lower()}{index:03d}' for index, name in enumerate(names, 1)]),
        ):
            result = conversion_routes.verify_bulk_registration_output(self.request(), Response(), 0)
        self.assertEqual(result['verification']['checked_records'], 22)
        stages = {stage['id']: stage for stage in result['verification']['stages']}
        self.assertEqual(stages['blank_user_name']['issues'], [22])
        self.assertEqual(stages['duplicate_user_name']['failed_records']['row_count'], 0)
        self.assertEqual(stages['duplicate_email']['failed_records']['row_count'], 21)
        self.assertEqual(len(result['username_changes']), 20)

    def test_verify_refreshes_generated_email_but_preserves_supplied_email(self):
        from app.services import bulk_registration_storage as storage
        frame = pd.DataFrame({
            'FIRST NAME': ['Ada', 'Bob'], 'LAST NAME': ['', ''],
            'FULL NAME': ['Ada Student', 'Bob Student'], 'Section': ['A', 'A'],
            'Class Number': ['Class I', 'Class I'], 'GENDER': ['Female', 'Male'],
            'CLASS': ['1', '1'], 'Gender Number': ['2', '1'],
            'section_index': ['1', '1'],
            'user_name': ['ada001', 'bob001'],
            'EMAIL': ['ada001@testschool.com', 'personal@example.org'],
            'admission_number': ['1', '2'],
        })
        state = storage.load_workspace(self.workspace_id)
        state['output'] = {'row_count': 2, 'rows': []}
        metadata = {
            'name': 'output.csv', 'school': {'school_name': 'Test School'},
            'generated_email_positions': [0],
        }
        storage.save_workspace(self.workspace_id, state, {
            '_output_authoritative': (metadata, frame.to_csv(index=False).encode()),
        })
        with (
            patch.object(conversion_routes, 'fetch_existing_usernames',
                         side_effect=[{'ada001'}, set(), set()]),
            patch.object(conversion_routes, 'fetch_existing_emails', return_value=set()),
            patch.object(conversion_routes, 'fetch_available_usernames',
                         return_value=['ada002']),
        ):
            result = conversion_routes.verify_bulk_registration_output(
                self.request(), Response(), 0,
            )

        rows = result['workspace']['output']['rows']
        email_index = result['workspace']['output']['columns'].index('EMAIL')
        self.assertEqual(rows[0][email_index], 'ada002@testschool.com')
        self.assertEqual(rows[1][email_index], 'personal@example.org')
