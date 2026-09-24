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
