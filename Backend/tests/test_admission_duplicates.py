import unittest
from io import BytesIO

import pandas as pd

from Backend.services.admission_mapping.admission_file_mapping import map_students, build_exports


# Protect whole-row deduplication order and duplicate/blank admission routing.
class AdmissionDuplicateTests(unittest.TestCase):
    def test_duplicate_matched_usernames_go_to_review_with_source_rows(self):
        school = pd.DataFrame({"admission": ["1", "2", "3"], "name": ["Alice", "Bob", "Wrong"]})
        dump = pd.DataFrame({"admission": ["1", "2", "3", "4", "5"],
                             "user_firstname": ["Alice", "Bob", "Carol", "Other", "Other"],
                             "username": ["shared", "shared", "shared", " shared ", ""]})
        result = map_students(school, dump, "admission", "admission", "username", "name")
        self.assertEqual(result.mapping_status.tolist(), ["Review", "Review", "Review"])
        self.assertEqual(result.mapping_reason.iloc[0], "duplicate username found; dump rows: 2, 3")
        self.assertEqual(result.mapping_reason.iloc[1], "duplicate username found; dump rows: 2, 3")
        self.assertEqual(result.mapping_reason.iloc[2],
                         "First name does not match between school and dump; dump row: 4")
        self.assertEqual(build_exports(result)["review.xlsx"]["count"], 3)

    def test_username_repeated_only_outside_matched_records_stays_matched(self):
        school = pd.DataFrame({"admission": ["1", "2"], "name": ["Alice", "Wrong"]})
        dump = pd.DataFrame({"admission": ["1", "2", "3"],
                             "user_firstname": ["Alice", "Bob", "Other"],
                             "username": ["shared", "shared", "shared"]})
        result = map_students(school, dump, "admission", "admission", "username", "name")
        self.assertEqual(result.mapping_status.tolist(), ["Matched", "Review"])

    def test_matched_user_id_is_exported_as_text(self):
        school = pd.DataFrame({"admission": ["1", "2", "3", "4", "5"],
                               "name": ["Alice", "Wrong", "Nobody", "Dan", "Eve"]})
        dump = pd.DataFrame({"admission": ["1", "2", "4", "4", "5"],
                             "user_firstname": ["Alice", "Bob", "Dan", "Dan", "Eve"],
                             "username": ["alice1", "bob2", "dan3", "dan4", "eve5"],
                             "user_id": ["001234567890123456789", "2", "3", "4", None]})
        result = map_students(school, dump, "admission", "admission", "username", "name")
        self.assertEqual(result.mapping_user_id.tolist(), ["001234567890123456789", "", "", "", ""])
        matched = pd.read_excel(BytesIO(build_exports(result)["matched.xlsx"]["data"]),
                                dtype=str, keep_default_na=False)
        self.assertNotIn("mapping_reason", matched.columns)
        self.assertEqual(matched.mapping_status.tolist(),
                         ["Matched — Admission number and first name match"] * 2)
        self.assertEqual(matched.mapping_user_id.tolist(), ["001234567890123456789", ""])
        self.assertEqual(matched.mapping_username.tolist(), ["alice1", "eve5"])

    def test_single_occurrence_compares_actual_first_names(self):
        school = pd.DataFrame({"admission": ["1", "2", "3", "4", "5"],
                               "name": [" ALICE ", "Bob", "", "Carol", "Nobody"]})
        dump = pd.DataFrame({"admission": ["1", "2", "3", "4"],
                             "firstName": ["alice", "Robert", None, ""],
                             "username": ["account_99", "bob2", "empty3", "carol4"]})
        result = map_students(school, dump, "admission", "admission", "username", "name",
                              dump_first_name_column="firstName")
        self.assertEqual(result.mapping_status.tolist(),
                         ["Matched", "Review", "Review", "Review", "Not Matched"])
        self.assertEqual(result.mapping_username.iloc[0], "account_99")
        self.assertEqual(result.mapping_dump_first_name.tolist(), ["alice", "robert", "", "", ""])
        self.assertEqual(result.mapping_reason.iloc[2], "School firstName missing; dump row: 4")
        for position, dump_row, reason in [
            (1, 3, "First name does not match between school and dump"),
            (3, 5, "Dump first name missing"),
        ]:
            self.assertEqual(result.mapping_reason.iloc[position],
                             f"{reason}; dump row: {dump_row}")
            self.assertEqual(result.mapping_dump_row.iloc[position], dump_row)
        self.assertEqual(build_exports(result)["review.xlsx"]["count"], 3)

    def test_single_occurrence_first_name_match_is_case_insensitive(self):
        school = pd.DataFrame({"admission": ["1", "2", "3"],
                               "name": ["ALICE", "bob", "CaRoL Smith"]})
        dump = pd.DataFrame({"admission": ["1", "2", "3"],
                             "user_firstname": ["alice", "BOB", "carol"],
                             "username": ["alice1", "bob2", "carol3"]})
        result = map_students(school, dump, "admission", "admission", "username", "name",
                              name_is_full=True)
        self.assertEqual(result.mapping_status.tolist(), ["Matched"] * 3)
        self.assertEqual(result.mapping_dump_first_name.tolist(), ["alice", "bob", "carol"])
        matched = pd.read_excel(BytesIO(build_exports(result)["matched.xlsx"]["data"]),
                                dtype=str, keep_default_na=False)
        self.assertEqual(matched.mapping_dump_first_name.tolist(), ["alice", "bob", "carol"])

    def test_missing_school_first_name_always_requires_review(self):
        school = pd.DataFrame({"admission": ["1", "2", "3", "4", "5", "5"],
                               "name": ["", None, " \t ", float("nan"), "", "Other"]})
        dump = pd.DataFrame({"admission": ["1", "3", "3"],
                             "user_firstname": ["Alice", "Bob", "Bob"],
                             "username": ["alice1", "bob1", "bob2"]})
        for full_name in (False, True):
            with self.subTest(full_name=full_name):
                result = map_students(school, dump, "admission", "admission", "username", "name",
                                      name_is_full=full_name)
                self.assertEqual(result.mapping_status.tolist(), ["Review"] * 6)
                self.assertTrue(result.mapping_reason.iloc[:5].str.contains("School firstName missing").all())
                self.assertIn("more than one occurrence; dump rows: 3, 4", result.mapping_reason.iloc[2])
                self.assertIn("admission number duplicate", result.mapping_reason.iloc[4])
                self.assertEqual(build_exports(result)["review.xlsx"]["count"], 6)

    # Ensure identical copies collapse before remaining admission collisions are reviewed.
    def test_identical_rows_removed_before_admission_checks(self):
        school = pd.DataFrame({
            "admission": ["001", "001", "001", "002", "002", "003", "003"],
            "name": ["Alice", "Alice", "Alice", "Bob", "Different", "Carol", "Carol"],
            "class": ["1", "1", "1", "2", "2", "3", "4"],
        })
        original = school.copy()
        dump = pd.DataFrame({"admission": ["001", "002", "003"],
                             "user_firstname": ["Alice", "Bob", "Carol"], "username": ["alice1", "bob2", "carol3"]})
        result = map_students(school, dump, "admission", "admission", "username", "name")
        self.assertEqual(result.mapping_status.tolist(), ["Matched"] + ["Review"] * 4)
        self.assertEqual(result.attrs, {"duplicate_rows": 3, "dropped_rows": 2})
        pd.testing.assert_frame_equal(result[school.columns], school.drop_duplicates().reset_index(drop=True))
        pd.testing.assert_frame_equal(school, original)

    # Ensure blank admissions are handed off as unmatched while repeated admissions need review.
    def test_initial_school_duplicates_bypass_matching_and_missing_outcomes(self):
        school = pd.DataFrame({
            "admission": ["001", " 001 ", "missing", "missing", "002", "003", "004", "", None],
            "name": ["Alice", "Wrong", "A", "B", "Bob", "Wrong", "Nobody", "", ""],
        })
        dump = pd.DataFrame({"admission": ["001", "002", "003"],
                             "user_firstname": ["Alice", "Bob", "Carol"], "username": ["alice_1", "bob2", "carol3"]})
        result = map_students(school, dump, "admission", "admission", "username", "name")
        self.assertEqual(result.mapping_status.tolist(),
                         ["Review"] * 4 + ["Matched", "Review", "Not Matched", "Not Matched", "Not Matched"])
        self.assertTrue(result.mapping_reason.iloc[:4].str.startswith("admission number duplicate").all())
        self.assertEqual(result.mapping_reason.iloc[:4].tolist(), ["admission number duplicate"] * 4)
        self.assertEqual(result.mapping_reason.iloc[-2:].tolist(), ["Admission number missing"] * 2)
        self.assertTrue(result.mapping_dump_row.iloc[:4].eq("").all())
        self.assertTrue(result.mapping_username.iloc[:4].eq("").all())
        pd.testing.assert_frame_equal(result[school.columns], school)
        exports = build_exports(result)
        self.assertEqual([exports[name]["count"] for name in
                          ("matched.xlsx", "review.xlsx", "not_matched.xlsx")], [1, 5, 3])

    # Dump collisions must bypass name matching and retain all source row numbers.
    def test_duplicate_dump_admissions_go_to_review(self):
        school = pd.DataFrame({"admission": ["001", "1"], "name": ["Alice", "Bob"]})
        dump = pd.DataFrame({"admission": ["001", "1", " 001 ", "001"],
                             "user_firstname": ["Alice", "Bob", "Wrong", "Alice"], "username": ["alice1", "bob3", "wrong2", "alice1"]},
                            index=[10, 20, 30, 40])
        result = map_students(school, dump, "admission", "admission", "username", "name")
        self.assertEqual(result.mapping_status.tolist(), ["Review", "Matched"])
        self.assertEqual(result.mapping_reason.iloc[0], "more than one occurrence; dump rows: 2, 4, 5")
        self.assertEqual(result.mapping_dump_row.iloc[0], "2, 4, 5")
        self.assertEqual(result.mapping_dump_count.iloc[0], 3)
        self.assertEqual(result.mapping_username.iloc[0], "")
        self.assertEqual(build_exports(result)["review.xlsx"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
