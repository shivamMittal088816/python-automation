"""Split classified rows into the three downloadable result workbooks."""

import pandas as pd

from .admission_workbook import build_workbook

def build_exports(result: pd.DataFrame) -> dict:
    """Return three independent workbooks, including headers for empty groups."""
    exports = {}
    for status, filename in (
        ("Matched", "matched.xlsx"),
        ("Review", "review.xlsx"),
        ("Not Matched", "not_matched.xlsx"),
    ):
        rows = result.loc[result["mapping_status"].eq(status)].copy()
        rows["mapping_status"] = rows["mapping_status"] + " — " + rows["mapping_reason"]
        rows = rows.drop(columns="mapping_reason")
        exports[filename] = build_workbook(rows, status)
    return exports

# Purpose: Split classified rows into the three downloadable result workbooks.
# Its public interface includes build_exports.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.scripts.admission_mapping.admission_file_mapping, app.scripts.admission_mapping_cli, app.services.admission_mapping.admission_file_mapping.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
