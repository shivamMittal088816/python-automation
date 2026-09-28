# Shared Excel writer used by initial exports and manual preview transfers.
# Returns workbook bytes and a row count; it does not save a file on disk.

"""Excel serialization shared by admission mapping and manual review."""

from io import BytesIO

import pandas as pd


# Serialize a DataFrame to in-memory XLSX bytes; formula-like uploaded strings remain literal text.
def build_workbook(rows: pd.DataFrame, sheet_name: str) -> dict:
    """Serialize rows while preserving uploaded text as literal Excel values."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        rows.to_excel(writer, sheet_name=sheet_name, index=False)
        for cells in writer.sheets[sheet_name].iter_rows():
            for cell in cells:
                if cell.data_type == "f":
                    cell.data_type = "s"
    return {"data": buffer.getvalue(), "count": len(rows)}

# Purpose: Excel serialization shared by admission mapping and manual review.
# Its public interface includes build_workbook.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.admission_mapping.admission_result_exports, app.services.email_mapping.email_result_exports, app.services.full_name_class_mapping.full_name_class_result_exports.
# It also has 1 additional direct importer in the backend.
# Tests and higher-level workflows exercise this behavior through its public callers.
