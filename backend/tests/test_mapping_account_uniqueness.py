"""Check account conflicts within each mapping stage."""
from io import BytesIO
import unittest

import pandas as pd

from app.services.admission_mapping.account_duplicates import duplicate_account_positions
from app.services.admission_mapping.admission_mapping_pipeline import map_students
from app.services.email_mapping.email_file_mapping import map_by_email
from app.services.full_name_class_mapping.full_name_class_file_mapping import map_by_full_name_class


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
        for exports, prefix in (
                (map_by_email(school, dump, "email", "user_email", "name", school_index="914"), "email_"),
                (map_by_full_name_class(school, dump, "name", "class"), "full_name_class_")):
            self.assertEqual(exports[prefix + "matched.xlsx"]["count"], 0)
            self.assertEqual(exports[prefix + "review.xlsx"]["count"], 2)
            review = pd.read_excel(BytesIO(exports[prefix + "review.xlsx"]["data"]), dtype=str)
            status = 'email_mapping_status' if prefix == 'email_' else 'full_name_class_status'
            self.assertTrue(review[status].str.contains('Duplicate username or user ID', case=False).all())


if __name__ == "__main__":
    unittest.main()
