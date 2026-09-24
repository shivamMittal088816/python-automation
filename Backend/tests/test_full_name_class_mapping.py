"""Classification checks for the third mapping stage."""
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from Backend.services.full_name_class_mapping.full_name_class_file_mapping import map_by_full_name_class, read_saved_dump
from Backend.services.email_mapping.email_file_mapping import email_input_signature
from Backend.api import file_workflow_state as storage
from Backend.services.admission_mapping.admission_workbook import build_workbook
from Backend.services.full_name_class_mapping.full_name_class_second_round import map_sorted_full_name_class, map_second_round


class FullNameClassMappingTests(unittest.TestCase):
    def test_both_rounds_use_name_and_class_regardless_of_admission_number(self):
        school = pd.DataFrame({'name': ['Mary Ann'], 'classNumber': ['4']})
        empty_values = [None, float('nan'), pd.NA, '', '  ', 'NULL', ' null ']
        for mapper in (map_by_full_name_class, map_sorted_full_name_class):
            for admissions, expected in ((empty_values, 'review'),
                                         (empty_values + ['0017'], 'review'),
                                         (empty_values + ['0017', '0017'], 'review'),
                                         ([''], 'matched'),
                                         ([0], 'matched')):
                with self.subTest(mapper=mapper.__name__, admissions=admissions):
                    dump = pd.DataFrame({
                        'generated_col': ['maryann4'] * len(admissions),
                        'fullname': ['Ann Mary'] * len(admissions),
                        'user_edu_class': ['4'] * len(admissions),
                        'admission_number': admissions,
                        'user_name': [f'user{i}' for i in range(len(admissions))],
                        'user_id': [str(i) for i in range(len(admissions))],
                    })
                    result = mapper(school, dump, 'name', 'classNumber')
                    for group in ('matched', 'review', 'not_matched'):
                        self.assertEqual(result[f'full_name_class_{group}.xlsx']['count'], int(group == expected))
                    if expected == 'matched':
                        matched = pd.read_excel(BytesIO(result['full_name_class_matched.xlsx']['data']), dtype=str)
                        self.assertEqual(matched.iloc[0]['full_name_class_username'], f'user{len(admissions)-1}')
            result = mapper(school, dump.drop(columns='admission_number'), 'name', 'classNumber')
            self.assertEqual(result['full_name_class_matched.xlsx']['count'], 1)

    def test_second_round_sorts_characters_and_requires_class_match(self):
        school = pd.DataFrame({
            'name': ['  Mary\tAnn ', 'MARY ANN', 'Mary Annn', '', 'Mary Ann', 'Mary Ann'],
            'classNumber': ['04.0', '5', '4', '4', '', '4'],
        })
        dump = pd.DataFrame({'fullname': ['Myra Nan', 'Mary Ann'],
                             'user_edu_class': ['4', '6'],
                             'user_name': ['mary', 'other_class'], 'user_id': ['0017', '0018']})
        dump["admission_number"] = [str(i) for i in range(len(dump))]
        # Two identical candidate school accounts must still be reviewed.
        result = map_sorted_full_name_class(school, dump, 'name', 'classNumber')
        self.assertEqual([result[f'full_name_class_{group}.xlsx']['count']
                          for group in ('matched', 'review', 'not_matched')], [0, 2, 4])
        review = pd.read_excel(BytesIO(result['full_name_class_review.xlsx']['data']), dtype=str, keep_default_na=False)
        self.assertEqual(review.full_name_class_sorted_name.tolist(), ['aamnnry', 'aamnnry'])
        self.assertEqual(review.full_name_class_compared_class.tolist(), ['4', '4'])
        self.assertEqual(review.full_name_class_user_id.tolist(), ['0017', '0017'])
        self.assertNotIn('full_name_class_status', school)

    def test_second_round_fixed_dump_columns_compare_without_offset(self):
        school = pd.DataFrame({'name': ['Mary Ann', 'Alice Smith'], 'classNumber': ['4', '3']})
        dump = pd.DataFrame({'fullname': ['Myra Nan', 'Smith Alice'], 'user_edu_class': ['4.0', '2'],
                             'user_name': ['mary', 'alice'], 'user_id': ['0001', '0002']})
        dump["admission_number"] = [str(i) for i in range(len(dump))]
        result = map_sorted_full_name_class(school, dump, 'name', 'classNumber')
        self.assertEqual(result['full_name_class_matched.xlsx']['count'], 1)
        self.assertEqual(result['full_name_class_not_matched.xlsx']['count'], 1)
        matched = pd.read_excel(BytesIO(result['full_name_class_matched.xlsx']['data']), dtype=str, keep_default_na=False)
        self.assertEqual(matched.iloc[0]['name'], 'Mary Ann')
        self.assertEqual(matched.iloc[0]['full_name_class_user_id'], '0001')
        self.assertIn('Round 2', matched.iloc[0]['full_name_class_status'])

    def test_second_round_does_not_choose_an_ambiguous_dump_account(self):
        school = pd.DataFrame({'name': ['Mary Ann'], 'classNumber': ['4']})
        dump = pd.DataFrame({'fullname': ['Myra Nan', 'Mary Ann'], 'user_edu_class': ['4', '4'],
                             'user_name': ['one', 'two'], 'user_id': ['1', '2']})
        dump["admission_number"] = [str(i) for i in range(len(dump))]
        result = map_sorted_full_name_class(school, dump, 'name', 'classNumber')
        self.assertEqual(result['full_name_class_review.xlsx']['count'], 1)
        self.assertEqual(result['full_name_class_matched.xlsx']['count'], 0)

    def test_second_round_preserves_first_round_matches_and_reviews(self):
        school = pd.DataFrame({'name': ['Alice Smith', 'Bob Jones', 'Mary Ann'], 'classNumber': ['3', '4', '5']})
        dump = pd.DataFrame({'generated_col': ['alicesmith3', 'bobjones4', 'bobjones4', 'myranan5'],
                             'fullname': ['Alice Smith', 'Bob Jones', 'Bob Jones', 'Myra Nan'],
                             'user_edu_class': ['3', '4', '4', '5'],
                             'user_name': ['alice', 'bob1', 'bob2', 'mary'], 'user_id': ['1', '2', '3', '4']})
        dump["admission_number"] = [str(i) for i in range(len(dump))]
        first = map_by_full_name_class(school, dump, 'name', 'classNumber')
        second = map_second_round(first, dump, 'name', 'classNumber')
        self.assertEqual([second[f'full_name_class_{group}.xlsx']['count']
                          for group in ('matched', 'review', 'not_matched')], [2, 1, 0])
        matched = pd.read_excel(BytesIO(second['full_name_class_matched.xlsx']['data']), dtype=str, keep_default_na=False)
        self.assertEqual(matched.name.tolist(), ['Alice Smith', 'Mary Ann'])
        self.assertNotIn('Round 2', matched.iloc[0]['full_name_class_status'])
        self.assertEqual(first['full_name_class_not_matched.xlsx']['count'], 1)

    def test_saved_xlsx_dump_uses_selected_sheet(self):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            pd.DataFrame({"other": ["skip"]}).to_excel(writer, sheet_name="Other", index=False)
            pd.DataFrame({"generated_col": ["alicesmith3"],
                          "user_name": ["élève_user"], "user_id": ["17"]}).to_excel(
                              writer, sheet_name="Users", index=False)
        dump = read_saved_dump({"name": "school_dump.xlsx", "data": buffer.getvalue()}, "Users")
        self.assertEqual(dump.iloc[0]["generated_col"], "alicesmith3")
        self.assertEqual(dump.iloc[0]["user_name"], "élève_user")

    def test_unique_duplicate_missing_and_absent_generated_values(self):
        school = pd.DataFrame({
            "name": [" Alice Smith ", "Bob Jones", "Carol Lee", "", "Dave Kim"],
            "classNumber": [" 3 ", "4", "5", "6", ""],
        })
        dump = pd.DataFrame({
            "generated_col": ["alicesmith3", "bobjones4", "bobjones4"],
            "user_name": ["alice_user", "bob_1", "bob_2"],
            "user_id": ["17", "18", "19"],
        })
        dump["admission_number"] = [str(i) for i in range(len(dump))]
        result = map_by_full_name_class(school, dump, "name", "classNumber")
        self.assertEqual([result[f"full_name_class_{group}.xlsx"]["count"]
                          for group in ("matched", "review", "not_matched")], [1, 1, 3])
        matched = pd.read_excel(BytesIO(result["full_name_class_matched.xlsx"]["data"]),
                                dtype=str, keep_default_na=False)
        self.assertEqual(matched.iloc[0]["full_name_class_generated_value"], "alicesmith3")
        self.assertEqual(matched.iloc[0]["full_name_class_username"], "alice_user")
        self.assertEqual(matched.iloc[0]["full_name_class_user_id"], "17")
        review = pd.read_excel(BytesIO(result["full_name_class_review.xlsx"]["data"]),
                               dtype=str, keep_default_na=False)
        self.assertEqual(review.iloc[0]["full_name_class_generated_value"], "bobjones4")
        self.assertEqual(review.iloc[0]["full_name_class_username"], "")
        not_matched = pd.read_excel(BytesIO(result["full_name_class_not_matched.xlsx"]["data"]),
                                    dtype=str, keep_default_na=False)
        self.assertEqual(not_matched["full_name_class_generated_value"].tolist(), [
            "carollee5", "", ""])
        self.assertNotIn("full_name_class_status", school.columns)

    def test_generated_col_is_required(self):
        with self.assertRaisesRegex(ValueError, "generated_col"):
            map_by_full_name_class(pd.DataFrame({"name": ["A"], "class": ["1"]}),
                                   pd.DataFrame({"user_id": ["1"]}), "name", "class")

    def test_duplicate_matched_usernames_move_all_rows_to_review(self):
        school = pd.DataFrame({"name": ["Alice Smith", "Alice Smith", "Bob Jones"],
                               "classNumber": ["3", "3", "4"]})
        dump = pd.DataFrame({"generated_col": ["alicesmith3", "bobjones4"],
                             "user_name": ["alice_user", "bob_user"],
                             "user_id": ["1", "2"]})
        dump["admission_number"] = [str(i) for i in range(len(dump))]
        result = map_by_full_name_class(school, dump, "name", "classNumber")
        self.assertEqual(result["full_name_class_matched.xlsx"]["count"], 1)
        self.assertEqual(result["full_name_class_review.xlsx"]["count"], 2)
        review = pd.read_excel(BytesIO(result["full_name_class_review.xlsx"]["data"]),
                               dtype=str, keep_default_na=False)
        self.assertEqual(review.full_name_class_username.tolist(), ["alice_user", "alice_user"])
        self.assertTrue(all("Duplicate username" in status
                            for status in review.full_name_class_status))

    def test_results_survive_session_save_and_restore(self):
        school = pd.DataFrame({"name": ["Alice Smith"], "classNumber": ["3"]})
        dump = pd.DataFrame({"generated_col": ["alicesmith3"],
                             "user_name": ["alice_user"], "user_id": ["17"]})
        dump["admission_number"] = [str(i) for i in range(len(dump))]
        state = {
            "saved_admission_dump": {"name": "dump.csv", "data": dump.to_csv(index=False).encode(),
                                     "school_index": "914", "school_name": "Test School"},
            "admission_exports": {"not_matched.xlsx": build_workbook(school, "Not matched")},
            "admission_settings": {},
            "full_name_class_exports": map_by_full_name_class(school, dump, "name", "classNumber"),
        }
        state["email_source_signature"] = email_input_signature(state)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'session'
            storage.save_state(folder, state)
            restored = storage.load_state(folder)
            self.assertEqual(restored["full_name_class_exports"]["full_name_class_matched.xlsx"]["count"], 1)
            self.assertNotIn("full_name_class_matched.xlsx", restored["admission_exports"])


if __name__ == "__main__":
    unittest.main()
