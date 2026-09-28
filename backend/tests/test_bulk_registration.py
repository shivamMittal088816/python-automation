import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

import pandas as pd
from fastapi import HTTPException

from app.routes.bulk_registration import FilePathInput, load_path, preview_file, clear_workspace
from app.routes.bulk_registration import convert_file, get_school
from app.services.bulk_registration import (
    OUTPUT_HEADERS, FIXED_VALUES, apply_available_usernames, blank_first_name_records,
    convert_frame, export_frame, fetch_school, fill_blank_emails, verify_generated_usernames,
)
from app.mappings.bulk_registration.section import apply_section_ids
from app.repositories.username_repository import fetch_available_usernames, fetch_existing_usernames
from fastapi import UploadFile


class BulkRegistrationTests(unittest.TestCase):
    def setUp(self):
        def usernames(first_names):
            counts = {}
            result = []
            for first_name in first_names:
                prefix = first_name.strip().lower()
                counts[prefix] = counts.get(prefix, 0) + 1
                result.append(f'{prefix}{counts[prefix]:03d}')
            return result

        self.username_patch = patch(
            'app.routes.bulk_registration.compatibility.fetch_available_usernames',
            side_effect=usernames,
        )
        self.username_patch.start()

    def tearDown(self):
        self.username_patch.stop()

    def test_working_sheet_preview_and_conversion(self):
        data = BytesIO()
        with pd.ExcelWriter(data, engine='openpyxl') as writer:
            pd.DataFrame().to_excel(writer, sheet_name='Empty', index=False)
            pd.DataFrame({'FIRST NAME': ['Ada'], 'admission_number': ['001']}).to_excel(writer, sheet_name='Students', index=False)
        preview = preview_file('input.xlsx', data.getvalue())
        self.assertEqual(preview['sheets'], ['Empty', 'Students'])
        self.assertEqual(preview['sheet'], 'Empty')
        self.assertEqual(preview['row_count'], 0)
        selected = preview_file('input.xlsx', data.getvalue(), 'Students')
        self.assertEqual(selected['rows'], [['Ada', '001']])
        with self.assertRaises(HTTPException):
            preview_file('input.xlsx', data.getvalue(), 'Missing')
        with patch('app.routes.bulk_registration.school_routes.fetch_school', return_value={'school_index': '42', 'school_name': 'Test'}):
            uploaded = UploadFile(filename='input.xlsx', file=BytesIO(data.getvalue()))
            result = convert_file('42', 'preview', uploaded, None, 'Students')
            self.assertEqual(result['rows'][0][0], 'Ada')
            with TemporaryDirectory() as directory:
                path = Path(directory) / 'input.xlsx'
                path.write_bytes(data.getvalue())
                with patch('app.routes.bulk_registration.file_reading.settings.ALLOW_LOCAL_FILE_PATHS', True):
                    self.assertEqual(load_path(FilePathInput(path=str(path), sheet='Students'))['sheet'], 'Students')
                    result = convert_file('42', 'csv', None, str(path), 'Students')
                    self.assertIn(b'Ada', result.body)
                    with self.assertRaises(HTTPException):
                        convert_file('42', 'preview', None, str(path), 'Empty')

    def test_xlsx_preserves_formula_like_text_and_large_exports(self):
        from openpyxl import load_workbook
        output = convert_frame(pd.DataFrame({'FIRST NAME': ['=1+1'] * 2000, 'admission_number': ['001'] * 2000}),
                               {'school_index': '42', 'school_name': 'Test School'})
        workbook = load_workbook(BytesIO(export_frame(output, 'xlsx')), read_only=True)
        rows = list(workbook.active.iter_rows())
        self.assertEqual(len(rows), 2001)
        self.assertEqual(rows[-1][0].value, '=1+1')
        self.assertEqual(rows[-1][0].data_type, 's')
        self.assertEqual(rows[-1][20].value, '001')
        workbook.close()

    def test_invalid_source_does_not_query_database(self):
        with patch('app.routes.bulk_registration.school_routes.fetch_school') as fetch:
            with self.assertRaises(HTTPException) as error:
                convert_file('42', 'preview', None, None)
            self.assertEqual(error.exception.status_code, 400)
            fetch.assert_not_called()

    def test_conversion_rules_and_column_order(self):
        frame = pd.DataFrame({'FIRST NAME': ['Ada', 'Sam'], 'admission_number': ['001', '002'],
                              'year': ['1999', ''], 'SCHOOL': ['Wrong', 'Wrong'],
                              'School Number': ['999', '999'], 'user_package': ['12', '11']})
        output = convert_frame(frame, {'school_index': '42', 'school_name': 'Test School'})
        self.assertEqual(list(output.columns), OUTPUT_HEADERS)
        self.assertEqual(len(output.columns), 24)
        self.assertEqual(output['admission_number'].tolist(), ['001', '002'])
        self.assertEqual(output['FULL NAME'].tolist(), ['', ''])
        self.assertEqual(output['SCHOOL'].tolist(), ['Test School'] * 2)
        self.assertEqual(output['School Number'].tolist(), ['42'] * 2)
        for column, value in FIXED_VALUES.items():
            self.assertEqual(output[column].tolist(), [value] * 2)
        for password in output['PASSWORD']:
            self.assertRegex(password, r'^[1-9][0-9]{4}[1-9]$')

        restored_csv = pd.read_csv(BytesIO(export_frame(output, 'csv')), dtype=str, keep_default_na=False)
        pd.testing.assert_frame_equal(restored_csv, output)

        from openpyxl import load_workbook
        workbook = load_workbook(BytesIO(export_frame(output, 'xlsx')), read_only=True, data_only=False)
        password_column = OUTPUT_HEADERS.index('PASSWORD') + 1
        self.assertEqual(workbook.active.cell(2, password_column).value, output.iloc[0]['PASSWORD'])
        self.assertEqual(workbook.active.cell(2, password_column).data_type, 's')
        workbook.close()

    def test_conversion_sorts_by_first_name_case_insensitively_with_blanks_last(self):
        frame = pd.DataFrame({
            'FIRST NAME': ['charlie', '', ' Bob ', 'alice', 'ALICE'],
            'admission_number': ['003', '005', '002', '004', '001'],
        })

        output = convert_frame(frame, {'school_index': '42', 'school_name': 'Test School'})

        self.assertEqual(output['FIRST NAME'].tolist(), ['alice', 'ALICE', ' Bob ', 'charlie', ''])
        self.assertEqual(output['admission_number'].tolist(), ['004', '001', '002', '003', '005'])
        self.assertEqual(output.attrs['source_row_numbers'], [5, 6, 4, 2, 3])

        self.assertEqual(blank_first_name_records(output), [{
            'row_number': 3,
            'last_name': '',
            'full_name': '',
            'admission_number': '005',
            'status': 'Provide FIRST NAME for user_name generation',
        }])

        apply_available_usernames(output, ['alice001', 'alice002', 'bob001', 'charlie001'])
        self.assertEqual(
            output['user_name'].tolist(),
            ['alice001', 'alice002', 'bob001', 'charlie001', ''],
        )
        with self.assertRaisesRegex(ValueError, 'exhausted values 001 through 1999'):
            apply_available_usernames(output, ['alice001'])

    def test_available_username_query_uses_lowercase_ordered_prefixes(self):
        connection = MagicMock()
        connection.execute.return_value.all.return_value = [('aarav001',), ('aditya002',)]
        with patch('app.config.database.engine.connect') as connect:
            connect.return_value.__enter__.return_value = connection
            result = fetch_available_usernames([' Aarav ', 'ADITYA'])

        self.assertEqual(result, ['aarav001', 'aditya002'])
        statement, parameters = connection.execute.call_args.args
        self.assertIn('BETWEEN 1 AND 1999', str(statement))
        self.assertIn('LEFT JOIN users', str(statement))
        self.assertEqual(parameters, {'prefix_0': 'aarav', 'prefix_1': 'aditya'})

    def test_existing_username_query_uses_parameterized_in_values(self):
        connection = MagicMock()
        connection.execute.return_value.all.return_value = [('alice001',)]
        with patch('app.config.database.engine.connect') as connect:
            connect.return_value.__enter__.return_value = connection
            result = fetch_existing_usernames(['bob001', 'alice001', 'alice001', ''])

        self.assertEqual(result, {'alice001'})
        statement, parameters = connection.execute.call_args.args
        self.assertIn('WHERE u.user_name IN', str(statement))
        self.assertEqual(parameters, {'usernames': ['alice001', 'bob001']})

    def test_username_verification_reports_all_three_stages(self):
        output = convert_frame(pd.DataFrame({
            'FIRST NAME': ['Alice', 'Bob', 'Cara'],
        }), {'school_index': '42', 'school_name': 'Test School'})
        output['user_name'] = ['alice001', 'alice001', 'wrong001']

        result = verify_generated_usernames(output, {'alice001'})

        self.assertFalse(result['passed'])
        self.assertEqual(result['checked_usernames'], 3)
        self.assertEqual(result['stages'][0]['issues'], ['alice001'])
        self.assertEqual(result['stages'][1]['issues'], ['alice001'])
        self.assertEqual(result['stages'][2]['issues'], [
            {'first_name': 'Bob', 'username': 'alice001', 'username_prefix': 'alice'},
            {'first_name': 'Cara', 'username': 'wrong001', 'username_prefix': 'wrong'},
        ])

        self.assertEqual(result['stages'][0]['failed_records']['columns'], ['Preview row', *OUTPUT_HEADERS])
        self.assertEqual(result['stages'][0]['failed_records']['rows'], [
            [1, *output.iloc[0].tolist()], [2, *output.iloc[1].tolist()],
        ])
        self.assertEqual(result['stages'][1]['failed_records']['rows'], result['stages'][0]['failed_records']['rows'])
        # Alice shares Bob's duplicate username but passes the first-name check.
        self.assertEqual(result['stages'][2]['failed_records']['rows'], [
            [2, *output.iloc[1].tolist()], [3, *output.iloc[2].tolist()],
        ])

        passed = verify_generated_usernames(
            output.assign(user_name=['alice001', 'bob001', 'cara001']), set(),
        )
        self.assertTrue(passed['passed'])
        self.assertTrue(all(stage['failed_records']['row_count'] == 0 for stage in passed['stages']))

        missing_suffix = verify_generated_usernames(
            output.assign(user_name=['alice', 'bob001', 'cara001']), set(),
        )
        self.assertFalse(missing_suffix['stages'][2]['passed'])

    def test_username_verification_reports_blank_values_with_full_records(self):
        frame = pd.DataFrame({'FIRST NAME': ['Ada', '', 'Bob', 'Cara'],
                              'user_name': ['ada001', '', ' \t ', None],
                              'admission_number': ['001', '002', '003', '004']})
        result = verify_generated_usernames(frame, set())
        self.assertFalse(result['passed'])
        self.assertEqual(result['checked_usernames'], 4)
        self.assertEqual(len(result['stages']), 4)
        stage = result['stages'][-1]
        self.assertEqual(stage['issues'], [2, 3, 4])
        self.assertEqual(stage['failed_records']['rows'], [
            [2, '', '', '002'], [3, 'Bob', ' \t ', '003'], [4, 'Cara', '', '004'],
        ])
        self.assertTrue(all(stage['passed'] for stage in result['stages'][:-1]))

    def test_blank_emails_are_generated_from_username_and_school_name(self):
        output = convert_frame(pd.DataFrame({
            'FIRST NAME': ['Ada', 'Bob', 'Cara'],
            'EMAIL': ['', ' supplied@example.org ', ''],
        }), {'school_index': '42', 'school_name': 'Samsidh International School, Fatehabad'})
        apply_available_usernames(output, ['ADA001', 'bob001', 'Cara001'])

        fill_blank_emails(output, 'Samsidh International School, Fatehabad')

        self.assertEqual(output['EMAIL'].tolist(), [
            'ada001@samsidhinternationalschoolfatehabad.com',
            ' supplied@example.org ',
            'cara001@samsidhinternationalschoolfatehabad.com',
        ])

    def test_generated_emails_remove_spaces_and_punctuation_from_both_components(self):
        frame = pd.DataFrame({
            'EMAIL': ['', '', '', ''],
            'user_name': [' Jo.HN-_ 001! ', 'ÉVA\t002', 'A@B\\003', '!!!'],
        })

        fill_blank_emails(frame, " St. Mary's École - School! ")

        self.assertEqual(frame['EMAIL'].tolist(), [
            'john001@stmarysecoleschool.com',
            'eva002@stmarysecoleschool.com',
            'ab003@stmarysecoleschool.com',
            '',
        ])
        for email in frame['EMAIL'][:3]:
            self.assertRegex(email, r'^[a-z0-9]+@[a-z0-9]+\.com$')

    def test_email_generation_leaves_blank_when_username_is_unavailable(self):
        output = convert_frame(pd.DataFrame({
            'FIRST NAME': [''], 'EMAIL': [''],
        }), {'school_index': '42', 'school_name': 'École Test'})
        apply_available_usernames(output, [])

        fill_blank_emails(output, 'École Test')

        self.assertEqual(output['EMAIL'].tolist(), [''])


    def test_gender_number_is_derived_from_gender_header(self):
        frame = pd.DataFrame({
            'Gender Number': ['99', '99', '99', '99', '99'],
            'GENDER': ['Male', ' Female ', 'OTHERS', '', 'Unknown'],
        })

        output = convert_frame(frame, {'school_index': '42', 'school_name': 'Test School'})

        self.assertEqual(output['GENDER'].tolist(), ['Male', ' Female ', 'OTHERS', '', 'Unknown'])
        self.assertEqual(output['Gender Number'].tolist(), ['1', '2', '3', '', ''])

    def test_class_id_is_derived_from_class_number_header(self):
        class_names = [
            'Class I', 'Class II', 'Class III', 'Class IV', 'Class V', 'Class VI',
            'Class VII', 'Class VIII', 'Class IX', 'Class X', 'Class XI', 'Class XII',
            'Other', 'Nursery', 'LKG', 'UKG', 'Passed Out', 'KG', 'Pre Nursery',
            'Pre Primary', 'Pre School', 'Play Group', '', 'Unknown',
        ]
        frame = pd.DataFrame({'Class Number': class_names, 'CLASS': ['99'] * len(class_names)})

        output = convert_frame(frame, {'school_index': '42', 'school_name': 'Test School'})

        self.assertEqual(output['Class Number'].tolist(), class_names)
        self.assertEqual(output['CLASS'].tolist(), [str(value) for value in range(22)] + ['', ''])

    def test_blank_full_names_report_source_rows_and_skip_present_names(self):
        from app.services.bulk_registration import blank_full_name_records
        from app.routes.bulk_registration.conversion_routes import paginated_summary

        output = convert_frame(pd.DataFrame({
            'FIRST NAME': ['Zoe', 'Ada', 'Bob', 'Cara'],
            'LAST NAME': ['Smith', 'Jones', '', ''],
            'FULL NAME': ['', ' \t ', 'Bob B', None],
            'admission_number': ['001', '002', '003', '004'],
        }), {'school_index': '42', 'school_name': 'Test School'})
        records = blank_full_name_records(output)
        self.assertEqual([record['row_number'] for record in records], [3, 5, 2])
        self.assertEqual([record['admission_number'] for record in records], ['002', '004', '001'])
        self.assertEqual(records[0], {'row_number': 3, 'admission_number': '002',
                                     'first_name': 'Ada', 'last_name': 'Jones', 'status': 'Needs full name'})
        self.assertEqual(paginated_summary('input.csv', output, {}, None, 1, [])['blank_full_name_records'], records)

    def test_unknown_genders_report_students_with_original_source_rows(self):
        from app.mappings.bulk_registration.gender import missing_gender_records
        from app.routes.bulk_registration.conversion_routes import paginated_summary

        output = convert_frame(pd.DataFrame({
            'FIRST NAME': ['Zoe', 'Ada', 'Bob', 'Cara', 'Dan', 'Eve'],
            'LAST NAME': ['Smith', '', '', '', '', ''],
            'FULL NAME': ['', 'Ada Jones', '', '', '', ''],
            'admission_number': ['001', '002', '003', '004', '005', '006'],
            'GENDER': ['Unknown', 'F', ' MALE ', 'female', 'OTHERS', ' '],
        }), {'school_index': '42', 'school_name': 'Test School'})
        expected = [
            {'gender': 'F', 'full_name': 'Ada Jones', 'admission_number': '002',
             'row_number': 3, 'status': 'Gender not exist'},
            {'gender': '', 'full_name': 'Eve', 'admission_number': '006',
             'row_number': 7, 'status': 'Gender is blank'},
            {'gender': 'Unknown', 'full_name': 'Zoe Smith', 'admission_number': '001',
             'row_number': 2, 'status': 'Gender not exist'},
        ]
        self.assertEqual(missing_gender_records(output), expected)
        self.assertEqual(paginated_summary('input.csv', output, {}, None, 1, [])['missing_genders'], expected)
        restored = pd.read_csv(BytesIO(export_frame(output, 'csv')), dtype=str, keep_default_na=False)
        self.assertEqual(paginated_summary('input.csv', restored, {}, None, 1, [], [], expected)['missing_genders'], expected)

    def test_unknown_classes_report_students_with_original_source_rows(self):
        from app.mappings.bulk_registration.class_name import missing_class_records
        from app.routes.bulk_registration.conversion_routes import paginated_summary

        output = convert_frame(pd.DataFrame({
            'FIRST NAME': ['Zoe', 'Ada', 'Bob', 'Cara', 'Dan'],
            'LAST NAME': ['Smith', '', '', '', ''],
            'FULL NAME': ['', 'Ada Jones', '', '', ''],
            'admission_number': ['001', '002', '003', '004', '005'],
            'Class Number': ['Class XIII', 'Unknown', ' CLASS I ', '', 'Other'],
        }), {'school_index': '42', 'school_name': 'Test School'})
        expected = [
            {'class_name': 'Unknown', 'full_name': 'Ada Jones', 'admission_number': '002',
             'row_number': 3, 'status': 'Class not exist'},
            {'class_name': '', 'full_name': 'Cara', 'admission_number': '004',
             'row_number': 5, 'status': 'Class is blank'},
            {'class_name': 'Class XIII', 'full_name': 'Zoe Smith', 'admission_number': '001',
             'row_number': 2, 'status': 'Class not exist'},
        ]
        self.assertEqual(missing_class_records(output), expected)
        summary = paginated_summary('input.csv', output, {}, None, 1, [])
        self.assertEqual(summary['missing_classes'], expected)
        restored = pd.read_csv(BytesIO(export_frame(output, 'csv')), dtype=str, keep_default_na=False)
        self.assertEqual(paginated_summary('input.csv', restored, {}, None, 1, [], expected)['missing_classes'], expected)

    def test_section_ids_are_mapped_and_missing_sections_are_reported(self):
        output = convert_frame(
            pd.DataFrame({
                'FIRST NAME': ['Ada', 'Bob', 'Cara', 'Dan', 'Eve'],
                'LAST NAME': ['Lovelace', '', '', '', ''],
                'FULL NAME': ['', 'Bob B', 'Cara C', 'Dan D', 'Eve E'],
                'Section': [' A ', 'c', 'New Section', 'new  section', ''],
            }),
            {'school_index': '42', 'school_name': 'Test School'},
        )

        missing = apply_section_ids(output, [(1, 'A'), (2, 'C')])

        self.assertEqual(output['section_index'].tolist(), ['1', '2', '', '', ''])
        self.assertEqual(missing, [
            {'section': 'New Section', 'full_name': 'Cara C', 'row_number': 4},
            {'section': 'new section', 'full_name': 'Dan D', 'row_number': 5},
            {'section': '', 'full_name': 'Eve E', 'row_number': 6},
        ])

    def test_unknown_header_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unrecognized input headers'):
            convert_frame(pd.DataFrame({'extra': ['value']}), {'school_index': '42', 'school_name': 'Test'})

    def test_conversion_api(self):
        data = b'FIRST NAME,admission_number\nAda,001\n'
        def uploaded():
            return UploadFile(filename='students.csv', file=BytesIO(data))
        with patch('app.routes.bulk_registration.school_routes.fetch_school', return_value={'school_index': '42', 'school_name': 'My School'}):
            response = convert_file('42', 'preview', uploaded(), None)
            self.assertEqual(response['columns'], OUTPUT_HEADERS)
            self.assertEqual(response['rows'][0][13:15], ['My School', '42'])
            self.assertEqual(response['rows'][0][6], 'ada001@myschool.com')
            response = convert_file('42', 'xlsx', uploaded(), None)
            self.assertEqual(response.status_code, 200)
            self.assertIn('bulk-registration-42.xlsx', response.headers['content-disposition'])
            with TemporaryDirectory() as directory:
                path = Path(directory) / 'students.csv'
                path.write_bytes(data)
                with patch('app.routes.bulk_registration.file_reading.settings.ALLOW_LOCAL_FILE_PATHS', True):
                    response = convert_file('42', 'preview', None, str(path))
                    self.assertEqual(response['rows'][0][20], '001')
                    self.assertEqual(response['rows'][0][13], 'My School')

    def test_output_preview_is_paginated(self):
        rows = ''.join(f'Student {index:02d},{index:03d}\n' for index in range(1, 46))
        data = ('FIRST NAME,admission_number\n' + rows).encode()

        with patch('app.routes.bulk_registration.school_routes.fetch_school', return_value={'school_index': '42', 'school_name': 'My School'}):
            first = convert_file('42', 'preview', UploadFile(filename='students.csv', file=BytesIO(data)), None)
            third = convert_file('42', 'preview', UploadFile(filename='students.csv', file=BytesIO(data)), None, None, 3)

        self.assertEqual((first['page'], first['page_size'], first['total_pages']), (1, 20, 3))
        self.assertEqual(len(first['rows']), 20)
        self.assertEqual(first['rows'][0][0], 'Student 01')
        self.assertEqual(len(third['rows']), 5)
        self.assertEqual(third['rows'][0][0], 'Student 41')

        with patch('app.routes.bulk_registration.school_routes.fetch_school', return_value={'school_index': '42', 'school_name': 'My School'}):
            with self.assertRaises(HTTPException) as error:
                convert_file('42', 'preview', UploadFile(filename='students.csv', file=BytesIO(data)), None, None, 4)
        self.assertEqual(error.exception.status_code, 400)

    def test_input_and_outputs_are_persisted_as_manifest_snapshots(self):
        import json
        import app.services.bulk_registration_storage as storage

        with TemporaryDirectory() as directory, patch.object(storage, 'ROOT', Path(directory)):
            workspace_id = storage.create_workspace()
            storage.save_input(workspace_id, {'name': 'students.csv', 'sheet': None},
                               b'FIRST NAME,GENDER\nAda,Female\n')
            folder = Path(directory) / workspace_id
            manifest = json.loads((folder / 'state.json').read_text(encoding='utf-8'))
            self.assertTrue((folder / manifest['input']['file']).is_file())

            storage.save_output(workspace_id, 'preview', {'name': 'preview.csv'}, b'preview')
            storage.save_output(workspace_id, 'xlsx', {'name': 'output.xlsx'}, b'xlsx')
            manifest = json.loads((folder / 'state.json').read_text(encoding='utf-8'))
            self.assertEqual(set(manifest['outputs']), {'preview', 'xlsx'})
            for reference in manifest['outputs'].values():
                self.assertTrue((folder / reference['file']).is_file())
            clear_workspace(workspace_id)
            self.assertFalse(folder.exists())

    def test_bulk_workspaces_expire_after_24_hours_of_inactivity(self):
        import os
        import time
        import app.services.bulk_registration_storage as storage

        with TemporaryDirectory() as directory, patch.object(storage, 'ROOT', Path(directory)):
            workspace_id = storage.create_workspace()
            folder = Path(directory) / workspace_id
            manifest = folder / 'state.json'
            expired = time.time() - storage.WORKSPACE_TTL_SECONDS - 1
            os.utime(manifest, (expired, expired))

            with self.assertRaises(HTTPException) as error:
                storage.load_workspace(workspace_id)

            self.assertEqual(error.exception.status_code, 404)
            self.assertFalse(folder.exists())

    def test_school_verification(self):
        from sqlalchemy.exc import SQLAlchemyError
        connection = MagicMock()
        with patch('app.config.database.engine.connect') as connect:
            connect.return_value.__enter__.return_value = connection
            connection.execute.return_value.first.return_value = (' Test School ',)
            self.assertEqual(fetch_school(' 0042 '), {'school_index': '0042', 'school_name': 'Test School'})
            self.assertEqual(connection.execute.call_args.args[1], {'school_index': '0042'})
            for row in [None, (' ',), (None,)]:
                connection.execute.return_value.first.return_value = row
                with self.assertRaises(HTTPException) as error:
                    get_school('42')
                self.assertEqual(error.exception.status_code, 404 if row is None else 400)
            connect.side_effect = SQLAlchemyError('Unavailable')
            with self.assertRaises(HTTPException) as error:
                get_school('42')
            self.assertEqual(error.exception.status_code, 503)
        for index in ['', 'abc']:
            with self.assertRaises(HTTPException) as error:
                get_school(index)
            self.assertEqual(error.exception.status_code, 400)

    def test_csv_preserves_identifiers_and_limits_preview(self):
        result = preview_file('students.csv', b'id,name\n' + b'001,Student\n' * 25)
        self.assertEqual(result['row_count'], 25)
        self.assertEqual(len(result['rows']), 20)
        self.assertEqual(result['rows'][0], ['001', 'Student'])
        self.assertEqual((result['page'], result['page_size'], result['total_pages']), (1, 20, 2))
        second = preview_file('students.csv', b'id,name\n' + b'001,Student\n' * 25, page=2)
        self.assertEqual(len(second['rows']), 5)

    def test_xlsx(self):
        source = BytesIO()
        pd.DataFrame({'name': ['Student']}).to_excel(source, index=False)
        self.assertEqual(preview_file('students.xlsx', source.getvalue())['rows'], [['Student']])

    def test_invalid_files(self):
        for name, data in [('data.txt', b'text'), ('data.csv', b''),
                           ('data.csv', b'name\n'), ('data.xlsx', b'invalid')]:
            with self.subTest(name=name, data=data), self.assertRaises(HTTPException) as error:
                preview_file(name, data)
            self.assertEqual(error.exception.status_code, 400)

    def test_size_limit(self):
        with patch('app.routes.bulk_registration.file_reading.settings.MAX_UPLOAD_BYTES', 2):
            with self.assertRaises(HTTPException) as error:
                preview_file('data.csv', b'name\nStudent')
            self.assertEqual(error.exception.status_code, 413)

    def test_path_loading_and_disabled_policy(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'students.csv'
            path.write_text('id,name\n001,Student', encoding='utf-8')
            with patch('app.routes.bulk_registration.file_reading.settings.ALLOW_LOCAL_FILE_PATHS', True):
                self.assertEqual(load_path(FilePathInput(path=str(path)))['row_count'], 1)
            with patch('app.routes.bulk_registration.file_reading.settings.ALLOW_LOCAL_FILE_PATHS', False):
                with self.assertRaises(HTTPException) as error:
                    load_path(FilePathInput(path=str(path)))
                self.assertEqual(error.exception.status_code, 403)
