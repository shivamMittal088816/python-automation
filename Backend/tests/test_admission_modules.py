"""Check the public admission entry point after separating its implementation."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pandas as pd

from Backend.services.admission_mapping.admission_file_mapping import build_exports, map_students, read_file
from Backend.services.admission_mapping.admission_mapping_pipeline import map_students as pipeline_map_students


class AdmissionModuleTests(unittest.TestCase):
    """Exercise file boundaries, validation and both supported CLI entry styles."""

    def test_public_import_and_empty_exports(self):
        # Existing callers must reach the same pipeline and retain empty workbook headers.
        self.assertIs(map_students, pipeline_map_students)
        school = pd.DataFrame(columns=["admission", "name"])
        dump = pd.DataFrame(columns=["admission", "username", "user_firstname"])
        result = map_students(school, dump, "admission", "admission", "username", "name")
        self.assertEqual(result.attrs, {"duplicate_rows": 0, "dropped_rows": 0})
        self.assertTrue(all(export["count"] == 0 for export in build_exports(result).values()))

    def test_invalid_columns_are_rejected(self):
        # Validation must fail before matching or overwriting existing audit columns.
        school = pd.DataFrame({"admission": ["001"], "name": ["Alice"]})
        dump = pd.DataFrame({"admission": ["001"], "username": ["alice1"], "user_firstname": ["Alice"]})
        with self.assertRaisesRegex(ValueError, "Missing school columns"):
            map_students(school, dump, "missing", "admission", "username", "name")
        with self.assertRaisesRegex(ValueError, "already contains output columns"):
            map_students(school.assign(mapping_status="old"), dump,
                         "admission", "admission", "username", "name")

    def test_unique_admission_first_name_length_and_mismatch(self):
        for full_name in (False, True):
            with self.subTest(full_name=full_name):
                names = [" A ", "B.", " Li ", "C", "Dana"]
                if full_name:
                    names = [name.strip() + " Smith" for name in names]
                school = pd.DataFrame({"admission": ["1", "2", "3", "4", "5"], "name": names})
                dump = pd.DataFrame({"admission": ["1", "2", "3", "4", "5"],
                                     "user_firstname": ["a", "b.", "LI", "D", "Dana"],
                                     "username": ["a1", "b2", "li3", "d4", ""],
                                     "user_id": ["1", "2", "3", "4", "5"]})
                result = map_students(school, dump, "admission", "admission", "username", "name",
                                      name_is_full=full_name)
                self.assertEqual(result.mapping_status.tolist(), ["Review", "Review", "Matched", "Review", "Review"])
                self.assertEqual(result.mapping_user_id.tolist(), ["", "", "3", "", ""])
                self.assertEqual(result.mapping_reason.tolist(), [
                    "First name matches but is only 1 character; dump row: 2",
                    "First name matches but is only 1 character; dump row: 3",
                    "Admission number and first name match",
                    "First name does not match between school and dump; dump row: 5",
                    "Username missing; dump row: 6",
                ])

    def test_cli_and_reader_preserve_identifiers(self):
        # Run real CSV-to-XLSX workflows in both script and module modes.
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            school = folder / "school.csv"
            dump = folder / "dump.csv"
            school.write_text("admission_number,first_name\n001,Alice\n001,Alice\n", encoding="utf-8")
            dump.write_text("admission_number,user_name,user_firstname\n001,alice1,Alice\n", encoding="utf-8")
            self.assertEqual(read_file(school).iloc[0]["admission_number"], "001")
            for mode, entry in (("script", ["Backend/scripts/admission_mapping/admission_file_mapping.py"]),
                                ("module", ["-m", "Backend.scripts.admission_mapping.admission_file_mapping"])):
                output = folder / f"{mode}.xlsx"
                process = subprocess.run(
                    [sys.executable, "-B", *entry, "--school", str(school), "--dump", str(dump),
                     "--output", str(output)], cwd=root, capture_output=True, text=True,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertIn("Rows in duplicate groups: 2; rows dropped: 1", process.stdout)
                matched = read_file(folder / f"{mode}_matched.xlsx")
                self.assertEqual(matched["admission_number"].tolist(), ["001"])


if __name__ == "__main__":
    unittest.main()
