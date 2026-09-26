"""Coordinate validation, deduplication, lookup and classification in the required order."""

import pandas as pd

from .admission_input_validation import RESULT_COLUMNS, validate_inputs
from .admission_duplicate_checks import prepare_school_rows, review_duplicate_admissions, review_duplicate_usernames
from .admission_dump_lookup import build_dump_lookup
from .admission_row_classification import classify_school_rows

def map_students(
    school: pd.DataFrame,
    dump: pd.DataFrame,
    school_admission_column: str,
    dump_admission_column: str,
    username_column: str,
    name_column: str,
    name_is_full: bool = False,
    dump_first_name_column: str = "user_firstname",
) -> pd.DataFrame:
    """Keep one copy of each school row and append auditable mapping results."""
    validate_inputs(school, dump, school_admission_column, dump_admission_column, username_column, name_column, dump_first_name_column)
    school, duplicate_rows, dropped_rows = prepare_school_rows(school, school_admission_column)
    lookup, counts, occurrence_rows = build_dump_lookup(dump, dump_admission_column, username_column, dump_first_name_column)
    records = classify_school_rows(school, school_admission_column, name_column, name_is_full,
                                  lookup, counts, occurrence_rows)

    # Join by row position, preserving every retained school row and appending the audit columns.
    result = pd.concat([
        school.reset_index(drop=True),
        pd.DataFrame(records, columns=RESULT_COLUMNS),
    ], axis=1)
    result = review_duplicate_admissions(result)
    result = review_duplicate_usernames(result)
    result.attrs["duplicate_rows"] = duplicate_rows
    result.attrs["dropped_rows"] = dropped_rows
    return result
