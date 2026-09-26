import unittest
from io import BytesIO

import pandas as pd

from app.services.full_name_class_mapping.full_name_class_file_mapping import (
    map_by_full_name_class,
    read_saved_dump,
)


class FullNameClassMappingTests(unittest.TestCase):
    def test_saved_xlsx_dump_uses_selected_sheet(self):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            pd.DataFrame({"generated_col": ["wrong"]}).to_excel(writer, index=False, sheet_name="First")
            pd.DataFrame({"generated_col": ["alicesmith3"]}).to_excel(writer, index=False, sheet_name="Chosen")
        dump = read_saved_dump({"name": "dump.xlsx", "data": buffer.getvalue()}, "Chosen")
        self.assertEqual(dump.iloc[0]["generated_col"], "alicesmith3")

    def test_unique_duplicate_missing_and_absent_generated_values(self):
        school = pd.DataFrame({"name": ["Alice Smith", "Bob Jones", "No Class", "Unknown"],
                               "classNumber": ["3", "4", "", "9"]})
        dump = pd.DataFrame({
            "generated_col": ["alicesmith3", "bobjones4", "bobjones4"],
            "user_name": ["alice_user", "bob_one", "bob_two"],
            "user_id": ["17", "18", "19"],
        })
        result = map_by_full_name_class(school, dump, "name", "classNumber")
        self.assertEqual([result[f"full_name_class_{group}.xlsx"]["count"]
                          for group in ("matched", "review", "not_matched")], [1, 1, 2])
        matched = pd.read_excel(BytesIO(result["full_name_class_matched.xlsx"]["data"]), dtype=str)
        self.assertEqual(matched.iloc[0]["full_name_class_user_id"], "17")

    def test_generated_col_is_required(self):
        with self.assertRaisesRegex(ValueError, "generated_col"):
            map_by_full_name_class(pd.DataFrame({"name": ["A"], "class": ["1"]}),
                                   pd.DataFrame({"user_id": ["1"]}), "name", "class")

    def test_duplicate_matched_usernames_move_all_rows_to_review(self):
        school = pd.DataFrame({"name": ["Alice Smith", "Alice Smith"], "classNumber": ["3", "3"]})
        dump = pd.DataFrame({"generated_col": ["alicesmith3"],
                             "user_name": ["alice_user"], "user_id": ["17"]})
        result = map_by_full_name_class(school, dump, "name", "classNumber")
        self.assertEqual(result["full_name_class_matched.xlsx"]["count"], 0)
        self.assertEqual(result["full_name_class_review.xlsx"]["count"], 2)


if __name__ == "__main__":
    unittest.main()
