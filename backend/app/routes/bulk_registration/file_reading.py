"""CSV/XLSX validation, parsing, path loading, and input previews."""
from io import BytesIO
from math import ceil
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


INPUT_PREVIEW_PAGE_SIZE = 20


def preview_file(name: str, data: bytes, sheet: str | None = None, page: int = 1):
    frame = read_frame(name, data, sheet, allow_empty_sheet=True)
    total_pages = max(1, ceil(len(frame) / INPUT_PREVIEW_PAGE_SIZE))
    if page < 1 or page > total_pages:
        raise HTTPException(400, 'The requested input preview page does not exist.')
    start = (page - 1) * INPUT_PREVIEW_PAGE_SIZE
    preview = frame.iloc[start:start + INPUT_PREVIEW_PAGE_SIZE]
    return {'name': name, 'size_bytes': len(data), 'row_count': len(frame),
            'columns': [str(column) for column in frame.columns],
            'rows': preview.fillna('').values.tolist(), 'page': page,
            'page_size': INPUT_PREVIEW_PAGE_SIZE, 'total_pages': total_pages,
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

# Purpose: CSV/XLSX validation, parsing, path loading, and input previews.
# Its public interface includes read_frame, preview_file, read_path.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.__init__, app.routes.bulk_registration.compatibility, app.routes.bulk_registration.conversion_routes.
# It also has 1 additional direct importer in the backend.
# Tests and higher-level workflows exercise this behavior through its public callers.
