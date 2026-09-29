import unittest

import pandas as pd

from app.services.bulk_registration_sanity import check_input
from app.mappings.bulk_registration.class_name import CLASS_NUMBERS


class InputSanityTests(unittest.TestCase):
    def test_class_must_match_a_stored_class(self):
        valid = list(CLASS_NUMBERS) + [' CLASS I ', 'Class XII', 'Nursery']
        invalid = ['', ' ', None, '1', '0', 'Class XIII', 'Unknown', 'Class I!']
        values = valid + invalid
        frame = pd.DataFrame({'FIRST NAME': ['Ada'] * len(values),
                              'FULL NAME': ['Ada Lovelace'] * len(values),
                              'Section': ['A'] * len(values),
                              'Class Number': values, 'GENDER': ['Female'] * len(values)})
        original = frame.copy(deep=True)
        result = check_input(frame)
        check = next(item for item in result['checks'] if item['id'] == 'class')
        self.assertEqual(check['failed_count'], len(invalid))
        self.assertFalse(check['passed'])
        self.assertEqual(result['failed_count'], len(invalid))
        self.assertTrue(all(not row['problems'] for row in result['rows'][:len(valid)]))
        for row in result['rows'][len(valid):]:
            self.assertEqual(row['problems'], ['Class Number missing or invalid: use a stored class name'])
        pd.testing.assert_frame_equal(frame, original)

    def test_gender_must_match_one_of_three_mapped_values(self):
        values = ['Male', 'Female', 'Others', ' MALE ', 'female', 'oThErS',
                  '', ' ', None, 'Other', 'M', 'F', '1', 'Unknown', 'Female!']
        frame = pd.DataFrame({'FIRST NAME': ['Ada'] * len(values),
                              'FULL NAME': ['Ada Lovelace'] * len(values),
                              'Section': ['A'] * len(values),
                              'Class Number': ['Class I'] * len(values), 'GENDER': values})
        original = frame.copy(deep=True)
        result = check_input(frame)
        gender = next(check for check in result['checks'] if check['id'] == 'gender')
        self.assertEqual(gender['failed_count'], 9)
        self.assertFalse(gender['passed'])
        self.assertEqual(result['failed_count'], 9)
        self.assertTrue(all(not row['problems'] for row in result['rows'][:6]))
        for row in result['rows'][6:]:
            self.assertEqual(row['problems'], ['Gender missing or invalid: use Male, Female or Others'])
        pd.testing.assert_frame_equal(frame, original)

    def test_preview_preserves_all_input_columns_and_values_in_order(self):
        frame = pd.DataFrame({'Status': ['source status'], 'CONTACT': ['001234'],
                              'FIRST NAME': ['Ada1'], 'Custom field': [None],
                              'Row number': ['original row'], 'house': ['Blue']})
        result = check_input(frame)
        self.assertEqual(result['columns'], list(frame.columns))
        self.assertEqual(result['rows'][0]['values'],
                         ['source status', '001234', 'Ada1', '', 'original row', 'Blue'])
        self.assertEqual(result['rows'][0]['row_number'], 2)
        self.assertTrue(result['rows'][0]['problems'])

    def test_checks_all_rows_and_flags_every_duplicate(self):
        rows = [{'FIRST NAME': 'Ada', 'FULL NAME': 'Ada Lovelace',
                 'Section': 'A', 'Class Number': 'Class I', 'GENDER': 'Female',
                 'EMAIL': f'ada{i}@example.com'} for i in range(25)]
        rows[24].update({'EMAIL': ' ADA0@EXAMPLE.COM ', 'FIRST NAME': '  ',
                         'FULL NAME': None, 'Section': '', 'Class Number': '', 'GENDER': ''})
        result = check_input(pd.DataFrame(rows))
        self.assertEqual(result['row_count'], 25)
        self.assertEqual(result['failed_count'], 2)
        self.assertEqual(result['rows'][24]['row_number'], 26)
        self.assertEqual(len(result['rows'][24]['problems']), 6)
        self.assertEqual(result['rows'][0]['problems'], ['Duplicate email in input file'])
        self.assertEqual(result['checks'][-1]['failed_count'], 2)

    def test_missing_columns_and_blank_emails(self):
        result = check_input(pd.DataFrame({'EMAIL': ['', ' ']}))
        self.assertTrue(result['checks'][-1]['passed'])
        self.assertEqual(result['failed_count'], 2)
        self.assertTrue(all(check['failed_count'] == 2 for check in result['checks'][:5]))
        self.assertTrue(all(check['passed'] for check in result['checks'][5:]))

    def test_name_characters_flag_each_field_without_changing_input(self):
        for column, key in [('FIRST NAME', 'first_name'), ('LAST NAME', 'last_name'),
                            ('FULL NAME', 'full_name')]:
            for value in ['Ada1', 'Anne-Marie', "O\'Neil", 'Ada.', 'José', 'Ada🙂',
                          'Ada\tLovelace', 'Ada\nLovelace', 'Ada\u00a0Lovelace']:
                with self.subTest(column=column, value=value):
                    frame = pd.DataFrame({'FIRST NAME': ['Ada'], 'LAST NAME': ['Lovelace'],
                                          'FULL NAME': ['Ada Lovelace'], 'Section': ['A'],
                                          'Class Number': ['Class I'], 'GENDER': ['Female']})
                    frame[column] = value
                    original = frame.copy(deep=True)
                    result = check_input(frame)
                    self.assertEqual(result['failed_count'], 1)
                    self.assertEqual(len(result['rows'][0]['problems']), 1)
                    check = next(item for item in result['checks'] if item['id'] == f'{key}_characters')
                    self.assertEqual(check['failed_count'], 1)
                    pd.testing.assert_frame_equal(frame, original)

    def test_mixed_case_and_spaces_are_valid_name_characters(self):
        frame = pd.DataFrame({'FIRST NAME': ['aDA'], 'LAST NAME': ['de Souza'],
                              'FULL NAME': ['aDA Mary de Souza'], 'Section': ['A'],
                              'Class Number': ['Class I'], 'GENDER': ['Female']})
        self.assertEqual(check_input(frame)['failed_count'], 0)

    def test_all_fields_are_trimmed_before_checks_and_preview(self):
        frame = pd.DataFrame({'FIRST NAME': [' \tAda\n'], 'LAST NAME': [' de Souza '],
                              'FULL NAME': [' Ada de Souza '], 'Section': [' A '],
                              'Class Number': [' Class I '], 'GENDER': [' Female '],
                              'EMAIL': [' ada@example.com '], 'CONTACT': [' 001234 '],
                              'Custom field': ['  keep  internal spaces  ']})
        original = frame.copy(deep=True)
        result = check_input(frame)
        self.assertEqual(result['failed_count'], 0)
        self.assertEqual(result['rows'][0]['values'],
                         ['Ada', 'de Souza', 'Ada de Souza', 'A', 'Class I', 'Female',
                          'ada@example.com', '001234', 'keep  internal spaces'])
        self.assertEqual(result['rows'][0]['first_name'], 'Ada')
        pd.testing.assert_frame_equal(frame, original)

    def test_first_name_internal_spaces_fail_after_trimming(self):
        frame = pd.DataFrame({'FIRST NAME': [' Ada Mary ', '   '],
                              'FULL NAME': ['Ada Mary', 'Ada Mary'], 'Section': ['A', 'A'],
                              'Class Number': ['Class I', 'Class I'], 'GENDER': ['Female', 'Female']})
        result = check_input(frame)
        self.assertEqual(result['failed_count'], 2)
        self.assertEqual(result['rows'][0]['first_name'], 'Ada Mary')
        self.assertEqual(result['rows'][0]['problems'],
                         ['First name: only A-Z and a-z (no spaces) allowed'])
        self.assertEqual(result['rows'][1]['problems'], ['First name missing'])

    def test_existing_input_username_fails_sanity(self):
        frame = pd.DataFrame({
            'FIRST NAME': ['Ada', 'Bob'],
            'FULL NAME': ['Ada A', 'Bob B'],
            'Section': ['A', 'A'],
            'Class Number': ['Class I', 'Class I'],
            'GENDER': ['Female', 'Male'],
            'user_name': [' existing001 ', ''],
        })

        result = check_input(frame)
        check = next(item for item in result['checks'] if item['id'] == 'username')

        self.assertEqual(check['failed_count'], 1)
        self.assertEqual(result['rows'][0]['username'], 'existing001')
        self.assertEqual(result['rows'][0]['problems'], [
            'Username already present in input file; leave it blank for generation',
        ])
        self.assertEqual(result['rows'][1]['problems'], [])

    def test_nonblank_input_email_must_follow_valid_format(self):
        values = ['name@domain.com', 'first.last+tag@sub.domain.co.in', '', 'plainaddress',
                  '@domain.com', 'name@domain', 'name@.com', 'name domain@example.com']
        frame = pd.DataFrame({
            'FIRST NAME': ['Ada'] * len(values),
            'FULL NAME': ['Ada Lovelace'] * len(values),
            'Section': ['A'] * len(values),
            'Class Number': ['Class I'] * len(values),
            'GENDER': ['Female'] * len(values),
            'EMAIL': values,
        })

        result = check_input(frame)
        check = next(item for item in result['checks'] if item['id'] == 'email_format')

        self.assertEqual(check['failed_count'], 5)
        self.assertTrue(all(not result['rows'][position]['problems'] for position in range(3)))

    def test_valid_input_passes_without_mutation(self):
        frame = pd.DataFrame({'FIRST NAME': ['Ada'], 'FULL NAME': ['Ada Lovelace'],
                              'Section': ['A'], 'Class Number': ['Class I'], 'GENDER': ['Female']})
        original = frame.copy(deep=True)
        result = check_input(frame)
        self.assertEqual(result['failed_count'], 0)
        self.assertTrue(all(check['passed'] for check in result['checks']))
        pd.testing.assert_frame_equal(frame, original)
