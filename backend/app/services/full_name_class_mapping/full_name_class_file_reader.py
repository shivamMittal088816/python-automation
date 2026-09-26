"""Read the saved admission dump for class and full name matching."""
from io import BytesIO
from pathlib import Path

import pandas as pd


def read_saved_dump(snapshot, sheet=None):
    """Read the saved admission dump with the same CSV/XLSX choice as admission mapping."""
    data = BytesIO(snapshot["data"])
    suffix = Path(snapshot["name"]).suffix.lower()
    if suffix == ".xlsx":
        return pd.read_excel(data, sheet_name=sheet if sheet is not None else 0,
                             dtype=str, keep_default_na=False).fillna("")
    if suffix == ".csv":
        return pd.read_csv(data, dtype=str, keep_default_na=False).fillna("")
    raise ValueError("The admission dump must be a CSV or XLSX file.")
