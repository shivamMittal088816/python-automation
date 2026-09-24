"""Regression checks for admission-to-email handoff and saved results."""
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from Backend.services.admission_mapping.admission_workbook import build_workbook
from Backend.services.email_mapping.email_file_mapping import map_by_email, sync_email_stage, email_input_signature
from Backend.api import file_workflow_state as storage


# Protect email classification, direct access and persisted result isolation.
class EmailHandoffTests(unittest.TestCase):
    # Verify email normalization, parameter binding and the empty-input short circuit.
    def test_email_dump_query_parameters(self):
        from Backend.repositories.email_dump_service import fetch_email_dump, QUERY
        engine = MagicMock()
        execute = engine.connect.return_value.__enter__.return_value.execute
        execute.return_value.fetchall.return_value = []
        with patch.dict(sys.modules, {"Backend.config.database": MagicMock(engine=engine)}):
            fetch_email_dump([" A@EXAMPLE.COM ", "a@example.com", "", None, "x'@example.com"])
            self.assertEqual(execute.call_args.args[1], {"emails": ["a@example.com", "x'@example.com"]})
            self.assertNotIn("x'@example.com", str(QUERY))
            self.assertNotIn("user_edu_school =", str(QUERY))
            execute.reset_mock()
            fetch_email_dump(["", None])
            execute.assert_not_called()

    def test_email_name_matches_require_same_school(self):
        school = pd.DataFrame({'email': ['a@x.com'], 'name': ['Alice']})
        for first_name in ('Alice', 'alice'):
            for index, dump_index, group in (('914', '914', 'matched'),
                                             ('914', '915', 'review'),
                                             ('914', None, 'review'),
                                             ('914', 'NULL', 'review'),
                                             (None, '914', 'review'),
                                             (None, None, 'review')):
                with self.subTest(first_name=first_name, index=index, dump_index=dump_index):
                    dump = pd.DataFrame({'user_email': ['a@x.com'], 'user_firstname': [first_name],
                                         'user_edu_school': [dump_index], 'user_id': ['001']})
                    result = map_by_email(school, dump, 'email', 'user_email', 'name', school_index=index)
                    self.assertEqual(result[f'email_{group}.xlsx']['count'], 1)
                    self.assertEqual(result['email_not_matched.xlsx']['count'], 0)
                    if group == 'review':
                        rows = pd.read_excel(BytesIO(result['email_review.xlsx']['data']), dtype=str)
                        self.assertIn('school', rows.iloc[0]['email_mapping_status'])
                        self.assertEqual(rows.iloc[0]['email_mapping_user_id'], '001')

    def test_school_index_change_invalidates_email_results(self):
        sync_email_stage(self.state)
        self.state['email_exports'] = {'old': True}
        self.state['saved_admission_dump']['school_index'] = '915'
        sync_email_stage(self.state)
        self.assertNotIn('email_exports', self.state)

    # Email mapping is available for any school with Not matched students.
    def test_email_stage_does_not_require_school_setting_or_confirmation(self):
        self.assertTrue(sync_email_stage(self.state))
        self.state["email_result_signature"] = (self.state["email_source_signature"], "email", "first", "email_first_name_school_v12", "914")
        self.state["email_exports"] = {"old": True}
        self.state["saved_email_dump"] = {"old": True}
        self.state["admission_settings"]["email_mapping_required"] = False
        self.assertTrue(sync_email_stage(self.state))
        self.assertIn("email_exports", self.state)
        self.state["admission_exports"]["not_matched.xlsx"]["count"] = 0
        self.assertFalse(sync_email_stage(self.state))
        self.assertNotIn("saved_email_dump", self.state)
        self.assertNotIn("email_exports", self.state)
        self.assertIn("not_matched.xlsx", self.state["admission_exports"])

    # Create independent school, dump and handoff fixtures for each test.
    def setUp(self):
        self.school = pd.DataFrame({"email": [" ALICE@EXAMPLE.COM ", "b@x.com", "dup@x.com", "", "missing@x.com"],
                                    "first": ["Alice", "Wrong", "Dan", "Eve", "Fred"]})
        self.dump = pd.DataFrame({"user_email": ["alice@example.com", "b@x.com", "dup@x.com", "dup@x.com"],
                                  "user_firstname": ["Alice", "Bob", "Dan", "Don"], "user_id": ["1", "2", "3", "4"]})
        self.dump["user_edu_school"] = "914"
        self.state = {
            "admission_exports": {
                "review.xlsx": build_workbook(self.school.iloc[:0], "Review"),
                "not_matched.xlsx": build_workbook(self.school, "Not matched"),
            },
            "saved_admission_dump": {"name": "dump.csv", "data": self.dump.to_csv(index=False).encode(),
                                      "school_index": "914", "school_name": "Test School"},
            "admission_settings": {"school_name_col": "first"},
        }

    # Check all result groups and ensure the caller input is not mutated.
    def test_classification_and_input_preservation(self):
        result = map_by_email(self.school, self.dump, "email", "user_email", "first", school_index="914")
        self.assertEqual([result[f"email_{name}.xlsx"]["count"] for name in ("matched", "review", "not_matched")], [1, 2, 2])
        matched = pd.read_excel(BytesIO(result["email_matched.xlsx"]["data"]), dtype=str)
        self.assertEqual(matched.iloc[0]["email_mapping_user_id"], "1")
        self.assertIn("email_mapping_status", matched.columns)
        self.assertNotIn("email_mapping_reason", matched.columns)
        self.assertEqual(matched.iloc[0]["email_mapping_status"],
                         "Matched — Email and first name match")
        self.assertEqual(matched.iloc[0]["email_mapping_dump_full_name"], "alice")
        review = pd.read_excel(BytesIO(result["email_review.xlsx"]["data"]),
                               dtype=str, keep_default_na=False)
        self.assertEqual(review.email_mapping_dump_full_name.tolist(), ["bob", ""])
        self.assertTrue(review.iloc[0]["email_mapping_status"].endswith(
                         "Email found; first name is different"))
        not_matched = pd.read_excel(BytesIO(result["email_not_matched.xlsx"]["data"]),
                                    dtype=str, keep_default_na=False)
        self.assertEqual(not_matched.email_mapping_dump_full_name.tolist(), ["", ""])
        self.assertNotIn("email_mapping_status", self.school.columns)

    def test_admission_audit_columns_do_not_enter_email_results(self):
        school = self.school.copy()
        admission_columns = ["mapping_username", "mapping_user_id", "mapping_dump_first_name",
                             "mapping_dump_row", "mapping_dump_count", "mapping_status",
                             "mapping_reason", "mapping_first_name", "mapping_admission_number"]
        for column in admission_columns:
            school[column] = "old admission result"
        result = map_by_email(school, self.dump, "email", "user_email", "first", school_index="914")
        for export in result.values():
            rows = pd.read_excel(BytesIO(export["data"]), dtype=str, keep_default_na=False)
            self.assertTrue(set(admission_columns).isdisjoint(rows.columns))
            self.assertIn("email_mapping_status", rows.columns)
        self.assertTrue(set(admission_columns).issubset(school.columns))

    # Protect first-name equality, punctuation/digits and null-email handling.
    def test_first_name_equality_without_regex(self):
        school = pd.DataFrame({"email": ["same", "different", "punctuation", "absent", None],
                               "name": [" Alice ", "Wrong", "Ann2", "Nobody", "Nobody"]})
        dump = pd.DataFrame({"user_email": ["same", "different", "punctuation", None],
                             "user_firstname": ["Alice", "Alice", "Ann2", "Nobody"]})
        dump["user_edu_school"] = "914"
        result = map_by_email(school, dump, "email", "user_email", "name", school_index="914")
        self.assertEqual([result[f"email_{name}.xlsx"]["count"] for name in
                          ("matched", "review", "not_matched")], [2, 1, 2])

    def test_pass_one_does_not_reorder_name_words(self):
        school = pd.DataFrame({"email": ["reordered", "different", "repeated"],
                               "name": ["Singh Ravi Kumar", "Ravi Other Singh", "Ravi Ravi Singh"]})
        dump = pd.DataFrame({"user_email": ["reordered", "different", "repeated"],
                             "user_firstname": ["Ravi Kumar Singh", "Ravi Kumar Singh", "Ravi Ravi Singh"]})
        dump["user_edu_school"] = "914"
        result = map_by_email(school, dump, "email", "user_email", "name", school_index="914")
        self.assertEqual(result["email_matched.xlsx"]["count"], 1)
        self.assertEqual(result["email_review.xlsx"]["count"], 2)
        matched = pd.read_excel(BytesIO(result["email_matched.xlsx"]["data"]), dtype=str)
        self.assertEqual(matched.iloc[0]["email_mapping_status"],
                         "Matched — Email and first name match")
        self.assertEqual(matched.iloc[0]["email_mapping_dump_full_name"], "ravi ravi singh")

    def test_duplicate_matched_usernames_move_all_rows_to_review(self):
        school = pd.DataFrame({"email": ["alice1@x.com", "alice2@x.com", "bob@x.com"],
                               "name": ["Alice Smith", "Alice Smith", "Bob Jones"]})
        dump = pd.DataFrame({"user_email": ["alice1@x.com", "alice2@x.com", "bob@x.com"],
                             "user_firstname": ["Alice Smith", "Alice Smith", "Bob Jones"],
                             "user_name": ["alice_user", "alice_user", "bob_user"],
                             "user_id": ["1", "1", "2"]})
        dump["user_edu_school"] = "914"
        result = map_by_email(school, dump, "email", "user_email", "name", school_index="914")
        self.assertEqual(result["email_matched.xlsx"]["count"], 1)
        self.assertEqual(result["email_review.xlsx"]["count"], 2)
        review = pd.read_excel(BytesIO(result["email_review.xlsx"]["data"]),
                               dtype=str, keep_default_na=False)
        self.assertEqual(review.email_mapping_username.tolist(), ["alice_user", "alice_user"])
        self.assertTrue(all("Duplicate username" in status
                            for status in review.email_mapping_status))

    def test_duplicate_school_emails_go_to_review_before_dump_lookup(self):
        school = pd.DataFrame({"email": [" Alice@X.COM ", "alice@x.com", "bob@x.com"],
                               "name": ["Alice Smith", "Alice Smith", "Bob Jones"]})
        dump = pd.DataFrame({"user_email": ["alice@x.com", "bob@x.com"],
                             "user_firstname": ["Alice Smith", "Bob Jones"],
                             "user_name": ["alice_user", "bob_user"]})
        dump["user_edu_school"] = "914"
        result = map_by_email(school, dump, "email", "user_email", "name", school_index="914")
        self.assertEqual(result["email_matched.xlsx"]["count"], 1)
        self.assertEqual(result["email_review.xlsx"]["count"], 2)
        review = pd.read_excel(BytesIO(result["email_review.xlsx"]["data"]),
                               dtype=str, keep_default_na=False)
        self.assertEqual(review.email_mapping_email.tolist(), ["alice@x.com", "alice@x.com"])
        self.assertTrue(all("Duplicate email in school file" in status
                            for status in review.email_mapping_status))

    def test_blank_emails_go_directly_to_not_matched(self):
        school = pd.DataFrame({"email": ["", "   ", None],
                               "name": ["Alice Smith", "Bob Jones", "Carol Lee"]})
        dump = pd.DataFrame({"user_email": ["alice@x.com"],
                             "user_firstname": ["Alice Smith"]})
        dump["user_edu_school"] = "914"
        result = map_by_email(school, dump, "email", "user_email", "name", school_index="914")
        self.assertEqual(result["email_review.xlsx"]["count"], 0)
        self.assertEqual(result["email_matched.xlsx"]["count"], 0)
        not_matched = pd.read_excel(BytesIO(result["email_not_matched.xlsx"]["data"]),
                                    dtype=str, keep_default_na=False)
        self.assertEqual(len(not_matched), 3)
        self.assertTrue(all("Email missing" in status
                            for status in not_matched.email_mapping_status))

    def test_missing_first_name_reason_identifies_source(self):
        school = pd.DataFrame({"email": ["school-missing", "dump-missing"],
                               "name": ["", "Alice Smith"]})
        dump = pd.DataFrame({"user_email": ["school-missing", "dump-missing"],
                             "user_firstname": ["Alice Smith", ""]})
        dump["user_edu_school"] = "914"
        result = map_by_email(school, dump, "email", "user_email", "name", school_index="914")
        review = pd.read_excel(BytesIO(result["email_review.xlsx"]["data"]),
                               dtype=str, keep_default_na=False)
        self.assertEqual([status.split("Email found; ", 1)[1]
                          for status in review.email_mapping_status], [
            "first name missing in school file", "first name missing in dump",
        ])

    # Invalidate email data when the admission misses change.
    def test_gate_and_invalidation(self):
        self.state["admission_exports"]["review.xlsx"]["count"] = 1
        self.assertTrue(sync_email_stage(self.state))
        self.state["email_result_signature"] = (self.state["email_source_signature"], "email", "first", "email_first_name_school_v12", "914")
        self.state["email_exports"] = {"placeholder": True}
        sync_email_stage(self.state)
        self.assertIn("email_exports", self.state)
        self.state["admission_exports"]["not_matched.xlsx"] = build_workbook(self.school.iloc[:1], "Not matched")
        sync_email_stage(self.state)
        self.assertNotIn("email_exports", self.state)
        self.state["admission_exports"]["not_matched.xlsx"]["count"] = 0
        self.assertFalse(sync_email_stage(self.state))

    # Round-trip admission and email files independently through session storage.
    def test_persistent_email_results(self):
        with tempfile.TemporaryDirectory() as directory:
            self.state["email_handoff_signature"] = email_input_signature(self.state)
            sync_email_stage(self.state)
            self.state["email_result_signature"] = (self.state["email_source_signature"], "email", "first", "email_first_name_school_v12", "914")
            self.state["email_exports"] = map_by_email(self.school, self.dump, "email", "user_email", "first", school_index="914")
            original_dump = self.state["saved_admission_dump"]["data"]
            self.state["saved_email_dump"] = {"name": "email_dump.csv", "data": b"user_email\nother@example.com\n"}
            folder = Path(directory) / 'session'
            storage.save_state(folder, self.state)
            restored = storage.load_state(folder)
            self.assertEqual(restored["saved_email_dump"]["data"], self.state["saved_email_dump"]["data"])
            self.assertEqual(restored["saved_admission_dump"]["data"], original_dump)
            self.assertNotEqual(restored["saved_email_dump"]["data"], original_dump)
            self.assertTrue(sync_email_stage(restored))
            self.assertEqual(restored["email_exports"]["email_matched.xlsx"]["count"], 1)
            self.assertNotIn("email_matched.xlsx", restored["admission_exports"])
            restored["admission_exports"]["not_matched.xlsx"] = build_workbook(self.school.iloc[:1], "Not matched")
            sync_email_stage(restored)
            storage.save_state(folder, restored)
            self.assertNotIn("email_exports", storage.load_state(folder))

if __name__ == "__main__":
    unittest.main()
