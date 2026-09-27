"""CSV/XLSX validation, parsing, path loading, and input previews."""
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import HTTPException

from app.config.settings import settings


def read_frame(name: str, data: bytes, sheet: str | None = None, allow_empty_sheet=False):
    suffix = Path(name).suffix.lower()
    if suffix not in ('.csv', '.xlsx'):
        raise HTTPException(400, 'Choose a CSV or XLSX file.')
    if not data:
        raise HTTPException(400, 'The selected file is empty.')
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(413, 'The selected file exceeds the upload size limit.')
    try:
        source = BytesIO(data)
        if suffix == '.csv':
            if sheet is not None:
                raise HTTPException(400, 'CSV files do not have worksheets.')
            frame = pd.read_csv(source, dtype=str, keep_default_na=False)
            frame.attrs.update(sheets=[], sheet=None)
        else:
            with pd.ExcelFile(source) as workbook:
                sheets = workbook.sheet_names
                selected = sheet if sheet is not None else sheets[0]
                if selected not in sheets:
                    raise HTTPException(400, 'The selected worksheet does not exist. Load the file again.')
                frame = pd.read_excel(workbook, sheet_name=selected, dtype=str, keep_default_na=False)
                frame.attrs.update(sheets=sheets, sheet=selected)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, 'Could not read this file. Check that it is a valid CSV or XLSX file.') from exc
    if frame.empty and not (suffix == '.xlsx' and allow_empty_sheet):
        raise HTTPException(400, 'The selected file contains no data rows.')
    return frame


def preview_file(name: str, data: bytes, sheet: str | None = None):
    frame = read_frame(name, data, sheet, allow_empty_sheet=True)
    return {'name': name, 'size_bytes': len(data), 'row_count': len(frame),
            'columns': [str(column) for column in frame.columns],
            'rows': frame.head(20).fillna('').values.tolist(),
            'sheets': frame.attrs['sheets'], 'sheet': frame.attrs['sheet']}


def read_path(value: str):
    if not settings.ALLOW_LOCAL_FILE_PATHS:
        raise HTTPException(403, 'File path loading is disabled on this app.')
    value = value.strip().strip('"')
    if not value or Path(value).suffix.lower() not in ('.csv', '.xlsx'):
        raise HTTPException(400, 'Enter a CSV or XLSX file path.')
    path = Path(value).expanduser()
    try:
        if not path.is_file():
            raise HTTPException(400, 'The path must point to a readable file.')
        with path.open('rb') as source:
            data = source.read(settings.MAX_UPLOAD_BYTES + 1)
    except OSError as exc:
        raise HTTPException(400, 'Could not load the selected file. Check that it exists and is readable.') from exc
    return path.name, data
