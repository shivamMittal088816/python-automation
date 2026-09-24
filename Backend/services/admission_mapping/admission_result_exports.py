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
