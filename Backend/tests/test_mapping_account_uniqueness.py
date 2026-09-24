"""Check account conflicts within stages and across the mapping workflow."""

from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from Backend.services.admission_mapping.account_duplicates import duplicate_account_positions
from Backend.services.admission_mapping.admission_mapping_pipeline import map_students
from Backend.services.admission_mapping.admission_workbook import build_workbook
from Backend.services.email_mapping.email_file_mapping import map_by_email
from Backend.services.full_name_class_mapping.full_name_class_file_mapping import map_by_full_name_class
from Backend.services.shared_mapping.mapping_account_uniqueness import review_duplicate_accounts


class MappingAccountUniquenessTests(unittest.TestCase):
    def test_either_identifier_conflicts_and_blank_identifiers_are_ignored(self):
        groups = ["Matched"] * 6 + ["Review"]
        usernames = ["same", " same ", "c", "d", "", None, "c"]
        ids = ["1", "2", "3", " 3 ", "", None, "3"]
        self.assertEqual(duplicate_account_positions(groups, usernames, ids), {0, 1, 2, 3})

    def test_user_id_duplicates_go_to_review_in_every_stage(self):
        school = pd.DataFrame({"admission": ["A1", "A2"], "name": ["Alice", "Bob"],
                               "email": ["a@example.test", "b@example.test"], "class": ["3", "4"]})
        dump = pd.DataFrame({"admission": ["A1", "A2"], "user_firstname": ["Alice", "Bob"],
                             "fullname": ["Alice", "Bob"], "user_name": ["alice", "bob"],
                             "user_id": ["50", "50"], "user_email": school.email,
                             "generated_col": ["alice3", "bob4"]})
        dump['admission_number'] = dump['admission']
        dump['user_edu_school'] = '914'
        result = map_students(school, dump, "admission", "admission", "user_name", "name")
        self.assertEqual(result.mapping_status.tolist(), ["Review", "Review"])
        self.assertTrue(result.mapping_reason.str.contains("duplicate user ID").all())
        for exports, prefix in ((map_by_email(school, dump, "email", "user_email", "name", school_index="914"), "email_"),
                                (map_by_full_name_class(school, dump, "name", "class"), "full_name_class_")):
            self.assertEqual(exports[prefix + "matched.xlsx"]["count"], 0)
            self.assertEqual(exports[prefix + "review.xlsx"]["count"], 2)
            self.assertEqual(exports[prefix + "not_matched.xlsx"]["count"], 0)
            review = pd.read_excel(BytesIO(exports[prefix + "review.xlsx"]["data"]), dtype=str)
            status = 'email_mapping_status' if prefix == 'email_' else 'full_name_class_status'
            self.assertTrue(review[status].str.contains('Duplicate username or user ID', case=False).all())

    def stage(self, prefix, name, username, user_id, reason=None):
        column = {"": "mapping", "email_": "email_mapping", "full_name_class_": "full_name_class"}[prefix]
        rows = pd.DataFrame({
            "name": [name], f"{column}_username": [username], f"{column}_user_id": [user_id],
            f"{column}_status": ["Matched"]})
        if reason:
            rows[f"{column}_status"] = "Review — " + reason
        empty = rows.iloc[:0]
        return {prefix + "matched.xlsx": build_workbook(empty if reason else rows, "Matched"),
                prefix + "review.xlsx": build_workbook(rows if reason else empty, "Review"),
                prefix + "not_matched.xlsx": build_workbook(empty, "Not Matched")}

    def reconcile(self, state):
        with patch("Backend.utils.file_snapshots.store_exports", side_effect=lambda exports: exports):
            return review_duplicate_accounts(state)

    def test_cross_stage_conflicts_move_all_rows_and_preserve_unrelated_accounts(self):
        for username, user_id in (("alice", "99"), ("different", "50")):
            with self.subTest(username=username, user_id=user_id):
                state = {"admission_exports": self.stage("", "Alice", "alice", "50"),
                         "email_exports": self.stage("email_", "Another student", username, user_id),
                         "full_name_class_exports": self.stage("full_name_class_", "Bob", "bob", "60")}
                self.assertEqual(self.reconcile(state), 2)
                for state_key, prefix in (("admission_exports", ""), ("email_exports", "email_")):
                    self.assertEqual(state[state_key][prefix + "matched.xlsx"]["count"], 0)
                    self.assertEqual(state[state_key][prefix + "review.xlsx"]["count"], 1)
                    rows = pd.read_excel(BytesIO(state[state_key][prefix + "review.xlsx"]["data"]), dtype=str)
                    self.assertIn("Duplicate username or user ID", rows.iloc[0].filter(like="status").iloc[0])
                self.assertEqual(state["full_name_class_exports"]["full_name_class_matched.xlsx"]["count"], 1)
                self.assertEqual(self.reconcile(state), 0)
                state["email_exports"] = self.stage("email_", "Another student", username, user_id)
                self.assertEqual(self.reconcile(state), 1)

    def test_local_duplicate_reviews_also_reserve_accounts(self):
        state = {"admission_exports": self.stage("", "Alice", "alice", "50", "duplicate user ID found"),
                 "email_exports": self.stage("email_", "Another", "other", "50")}
        self.assertEqual(self.reconcile(state), 1)
        self.assertEqual(state["email_exports"]["email_matched.xlsx"]["count"], 0)

    def test_nonduplicate_review_candidates_do_not_block_valid_matches(self):
        state = {"admission_exports": self.stage("", "Alice", "alice", "50", "Name mismatch"),
                 "email_exports": self.stage("email_", "Another", "alice", "50")}
        self.assertEqual(self.reconcile(state), 0)


if __name__ == "__main__":
    unittest.main()
