import unittest

import pandas as pd

from app.services.bulk_reg_final_verification import (
    repair_conflicting_usernames, verify_final_output,
)


class BulkRegistrationFinalVerificationTests(unittest.TestCase):
    def final_frame(self, values):
        frame = pd.DataFrame(values)
        defaults = {
            'LAST NAME': 'Student',
            'FULL NAME': 'Valid Student',
            'Section': 'A',
            'section_index': '1',
            'Class Number': 'Class I',
            'CLASS': '0',
            'GENDER': 'Female',
            'Gender Number': '2',
        }
        for column, value in defaults.items():
            if column not in frame:
                frame[column] = value
        return frame

    def test_reports_all_blank_and_duplicate_username_and_email_rows(self):
        frame = self.final_frame({
            'user_name': ['Ada001', ' ada001 ', '', 'Bob001', 'Cara001'],
            'EMAIL': ['one@example.com', 'two@example.com', ' ', ' SAME@example.com ',
                      'same@EXAMPLE.com'],
            'FIRST NAME': ['Ada', 'Ava', 'Blank', 'Bob', 'Cara'],
        })

        result = verify_final_output(frame)

        self.assertFalse(result['passed'])
        self.assertEqual(result['checked_records'], 5)
        self.assertEqual([stage['id'] for stage in result['stages'][:4]], [
            'blank_user_name', 'blank_email', 'duplicate_user_name', 'duplicate_email',
        ])
        self.assertEqual([stage['failed_records']['row_count'] for stage in result['stages'][:4]],
                         [1, 1, 2, 2])
        self.assertEqual(result['stages'][0]['issues'], [3])
        self.assertEqual(result['stages'][1]['issues'], [3])

    def test_passes_unique_nonblank_final_values(self):
        frame = self.final_frame({
            'FIRST NAME': ['Ada', 'Bob'],
            'user_name': ['ada001', 'bob001'],
            'EMAIL': ['ada@example.com', 'bob@example.com'],
        })

        result = verify_final_output(frame)

        self.assertTrue(result['passed'])
        self.assertTrue(all(stage['passed'] for stage in result['stages']))

    def test_fails_database_conflicts_and_username_first_name_mismatches(self):
        frame = self.final_frame({
            'FIRST NAME': ['Ada', 'Bob', 'Cara'],
            'user_name': ['ada001', 'alice002', 'cara'],
            'EMAIL': ['new@example.com', 'used@example.com', 'cara@example.com'],
        })

        result = verify_final_output(
            frame,
            existing_usernames={'ADA001'},
            existing_emails={' USED@example.com '},
        )
        stages = {stage['id']: stage for stage in result['stages']}

        self.assertFalse(result['passed'])
        self.assertEqual(stages['existing_user_name']['failed_records']['row_count'], 1)
        self.assertEqual(stages['existing_email']['failed_records']['row_count'], 1)
        self.assertEqual(stages['username_first_name_match']['failed_records']['row_count'], 2)
        self.assertEqual(
            [issue['username'] for issue in stages['username_first_name_match']['issues']],
            ['alice002', 'cara'],
        )

    def test_rechecks_all_final_name_and_mapping_sanity_rules(self):
        frame = pd.DataFrame({
            'FIRST NAME': ['', 'Ada Mary', 'Bob', 'Cara', 'Dan', 'Eve', 'Finn', 'Gia'],
            'LAST NAME': ['Valid', 'Valid', 'Smith2', 'Valid', 'Valid', 'Valid', 'Valid', 'Valid'],
            'FULL NAME': ['Valid Name', 'Valid Name', 'Valid Name', '', 'Cara3', 'Valid Name', 'Valid Name', 'Valid Name'],
            'Section': ['A', 'A', 'A', 'A', 'A', '', 'A', 'A'],
            'section_index': ['1', '1', '1', '1', '1', '', '1', '1'],
            'Class Number': ['Class I'] * 6 + ['', 'Class I'],
            'CLASS': ['0'] * 6 + ['', '0'],
            'GENDER': ['Female'] * 7 + ['Unknown'],
            'Gender Number': ['2'] * 7 + [''],
            'user_name': ['', 'adamary001', 'bob001', 'cara001', 'dan001', 'eve001', 'finn001', 'gia001'],
            'EMAIL': [f'user{index}@example.com' for index in range(8)],
        })

        result = verify_final_output(frame)
        stages = {stage['id']: stage for stage in result['stages']}

        for stage_id in (
            'first_name_required', 'first_name_characters', 'last_name_characters',
            'full_name_required', 'full_name_characters', 'section_index',
            'class_index', 'gender_index',
        ):
            self.assertFalse(stages[stage_id]['passed'], stage_id)
            self.assertEqual(stages[stage_id]['failed_records']['row_count'], 1)

    def test_final_nonblank_email_must_follow_valid_format(self):
        frame = self.final_frame({
            'FIRST NAME': ['Ada', 'Bob'],
            'user_name': ['ada001', 'bob001'],
            'EMAIL': ['ada@example.com', 'invalid-email'],
        })

        result = verify_final_output(frame)
        stage = next(stage for stage in result['stages'] if stage['id'] == 'email_format')

        self.assertFalse(stage['passed'])
        self.assertEqual(stage['issues'], [2])
        self.assertEqual(stage['failed_records']['row_count'], 1)

    def test_repairs_conflicts_until_usernames_are_unique_in_file_and_database(self):
        frame = pd.DataFrame({
            'FIRST NAME': ['Ada', 'Ada', 'Bob'],
            'user_name': ['ada001', 'ada001', 'bob001'],
            'admission_number': ['001', '002', '003'],
        })
        frame.attrs['source_row_numbers'] = [2, 3, 4]
        allocations = iter([
            ['ada002', 'ada003'],
            ['ada004', 'ada005'],
        ])
        database_results = iter([
            {'ada001'},
            {'ada002'},
            set(),
        ])

        changes = repair_conflicting_usernames(
            frame,
            lambda _names: next(allocations),
            lambda _usernames: next(database_results),
        )

        self.assertEqual(frame['user_name'].tolist(), ['ada004', 'ada005', 'bob001'])
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[0]['previous_username'], 'ada001')
        self.assertEqual(changes[0]['new_username'], 'ada004')
        self.assertIn('conflicted, so ada004 was generated and assigned', changes[0]['message'])

    def test_repairs_only_conflicting_rows_and_skips_valid_file_usernames(self):
        frame = pd.DataFrame({
            'FIRST NAME': ['Ada', 'Ada', 'Bob'],
            'user_name': ['ada001', 'ada001', 'bob001'],
            'admission_number': ['001', '002', '003'],
        })

        changes = repair_conflicting_usernames(
            frame,
            lambda names: ['ada002', 'ada003'] if len(names) == 2 else [],
            lambda _usernames: set(),
        )

        self.assertEqual(frame['user_name'].tolist(), ['ada002', 'ada003', 'bob001'])
        self.assertEqual([change['previous_username'] for change in changes], ['ada001', 'ada001'])
        self.assertNotIn('bob001', [change['previous_username'] for change in changes])
