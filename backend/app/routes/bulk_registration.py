"""Independent, stateless file intake for bulk registration."""
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from typing import Annotated, Literal
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from openpyxl.utils.exceptions import IllegalCharacterError

from app.config.settings import settings
from app.services.bulk_registration import SchoolNotFoundError, convert_frame, export_frame, fetch_school

router = APIRouter(prefix='/bulk-reg', tags=['Bulk registration'])


class FilePathInput(BaseModel):
    path: str
    sheet: str | None = None


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


@router.post('/files')
def upload_file(file: UploadFile = File(...), sheet: Annotated[str | None, Form()] = None):
    try:
        data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise HTTPException(400, 'Could not read the uploaded file.') from exc
    return preview_file(file.filename or '', data, sheet)


@router.post('/files/path')
def load_path(payload: FilePathInput):
    name, data = read_path(payload.path)
    return preview_file(name, data, payload.sheet)


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


@router.get('/schools/{school_index}')
def get_school(school_index: str):
    try:
        return fetch_school(school_index)
    except SchoolNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'School verification failed. Check the database connection and try again.') from exc


@router.post('/convert')
def convert_file(
    school_index: str = Form(...),
    file_format: Literal['preview', 'csv', 'xlsx'] = Form('preview'),
    file: UploadFile | None = File(None),
    path: str | None = Form(None),
    sheet: Annotated[str | None, Form()] = None,
):
    if (file is None) == (path is None):
        raise HTTPException(400, 'Provide either an uploaded file or a file path.')
    if file is not None:
        name = file.filename or ''
        try:
            data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
        except (OSError, ValueError) as exc:
            raise HTTPException(400, 'Could not read the uploaded file.') from exc
    else:
        name, data = read_path(path)
    frame = read_frame(name, data, sheet)
    school = get_school(school_index)
    try:
        output = convert_frame(frame, school)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if file_format == 'preview':
        return {'name': name, 'row_count': len(output), 'columns': list(output.columns),
                'rows': output.head(20).values.tolist(), 'school': school}
    filename = f'bulk-registration-{school["school_index"]}.{file_format}'
    media_type = ('text/csv' if file_format == 'csv' else
                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    try:
        exported = export_frame(output, file_format)
    except (ValueError, IllegalCharacterError) as exc:
        raise HTTPException(400, 'Could not create XLSX. Check for invalid spreadsheet characters or download CSV instead.') from exc
    return Response(exported, media_type=media_type,
                    headers={'Content-Disposition': f'attachment; filename="{filename}"',
                             'Cache-Control': 'no-store'})
