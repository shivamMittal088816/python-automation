"""Read school and dump spreadsheets without losing leading zeros."""

from pathlib import Path

import pandas as pd

def read_file(path: Path, sheet: str | None = None) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    elif path.suffix.lower() == ".xlsx":
        frame = pd.read_excel(
            path, sheet_name=sheet if sheet is not None else 0,
            dtype=str, keep_default_na=False,
        )
    else:
        raise ValueError(f"Unsupported file: {path}. Use .csv or .xlsx.")
    return frame.fillna("")

# Purpose: Read school and dump spreadsheets without losing leading zeros.
# Its public interface includes read_file.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.scripts.admission_mapping.admission_file_mapping, app.scripts.admission_mapping_cli, app.services.admission_mapping.admission_file_mapping.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
