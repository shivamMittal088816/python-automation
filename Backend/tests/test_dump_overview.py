"""School overview counts from CSV or XLSX dump rows."""
from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from Backend.api.file_workflow_helpers import class_section_table, dump_overview, inferred_school_index, school_class_statistics


class DumpOverviewTests(unittest.TestCase):
    def test_class_section_counts_and_school_index(self):
        rows = pd.DataFrame({
            "user_edu_school": ["738", "738", "738", "738", "738"],
            "user_edu_class": ["10", "2", "2", "2", ""],
            "user_edu_major": ["A", "B", "B", "A", ""],
            "user_package": ["14", "12", "14", "12", ""],
            "user_id": ["1", "2", "2", "3", ""],
        })
        table, students = dump_overview(rows)
        self.assertEqual(inferred_school_index(rows), "738")
        self.assertEqual(students, 4)
        self.assertEqual(table.to_dict("records"), [
            {"Class": "Class 3", "Sections": "A, B", "Packages": "12, 14", "Students": 2},
            {"Class": "Class 11", "Sections": "A", "Packages": "14", "Students": 1},
            {"Class": "Not specified", "Sections": "Not specified", "Packages": "Not specified", "Students": 1},
        ])

    def test_mixed_school_indices_are_not_inferred(self):
        rows = pd.DataFrame({"user_edu_school": ["738", "914"]})
        self.assertEqual(inferred_school_index(rows), "")

    def test_school_sheet_columns_can_be_selected(self):
        rows = pd.DataFrame({"Grade": ["2", "2", "10"],
                             "Division": ["B", "A", "C"]})
        table = class_section_table(rows, "Grade", "Division")
        self.assertEqual(table.to_dict("records"), [
            {"Class": "Class 2", "Sections": "A, B", "Students": 2},
            {"Class": "Class 10", "Sections": "C", "Students": 1},
        ])

    def test_dump_class_five_is_displayed_as_class_six(self):
        rows = pd.DataFrame({"user_edu_class": ["5"],
                             "user_edu_major": ["A"], "user_package": ["14"]})
        table, _ = dump_overview(rows)
        self.assertEqual(table.iloc[0]["Class"], "Class 6")

    def test_school_statistics_preserve_class_text_and_list_sections(self):
        rows = pd.DataFrame({
            "Class": ["Class III", "Class III", "Class IV", "Class III"],
            "Section": ["A", "B", "A", "A"],
        })
        table = school_class_statistics(rows, "Class", "Section")
        self.assertEqual(table.to_dict("records"), [
            {"Class": "Class III", "Students": 3, "Sections": "A, B"},
            {"Class": "Class IV", "Students": 1, "Sections": "A"},
        ])


if __name__ == "__main__":
    unittest.main()
