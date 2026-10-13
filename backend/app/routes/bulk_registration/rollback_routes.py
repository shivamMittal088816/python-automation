"""File intake endpoints for the rollback workflow."""

import csv
from itertools import chain
import os
from pathlib import Path
import tempfile
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.utils.exceptions import IllegalCharacterError
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from starlette.background import BackgroundTask

from app.config.settings import settings
from app.routes.bulk_registration.file_reading import preview_file
from app.routes.bulk_registration.models import SchoolInput
from app.routes.bulk_registration.school_routes import get_school
from app.repositories.rollback_dump_repository import stream_rollback_dump
from app.services import rollback as rollback_storage


router = APIRouter(prefix='/rollback')
ROLLBACK_COOKIE = '__Host-rollback-workspace' if settings.SESSION_COOKIE_SECURE else 'rollback_workspace'
DUMP_PREVIEW_PAGE_SIZE = 20


class RollbackSheetInput(BaseModel):
    sheet: str


def _safe_csv_cell(value):
    text_value = '' if value is None else str(value)
    if text_value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')):
        return "'" + text_value
    return text_value


def _export_dump_file(workspace_id, file_format):
    descriptor, name = tempfile.mkstemp(prefix='rollback-dump-', suffix=f'.{file_format}')
    os.close(descriptor)
    target = Path(name)
    try:
        with rollback_storage.open_dump_rows(workspace_id) as (columns, rows, _):
            if file_format == 'csv':
                with target.open('w', encoding='utf-8-sig', newline='') as output:
                    writer = csv.writer(output, lineterminator='\n')
                    writer.writerow([_safe_csv_cell(value) for value in columns])
                    for row in rows:
                        writer.writerow([_safe_csv_cell(value) for value in row])
            else:
                workbook = Workbook(write_only=True)
                sheet = workbook.create_sheet('Rollback dump')
                sheet.freeze_panes = 'A2'
                for row in chain([columns], rows):
                    cells = []
                    for value in row:
                        cell = WriteOnlyCell(sheet, value='' if value is None else str(value))
                        cell.data_type = 's'
                        cells.append(cell)
                    sheet.append(cells)
                workbook.save(target)
        return target
    except Exception:
        target.unlink(missing_ok=True)
        raise


def _set_cookie(response, workspace_id):
    response.set_cookie(
        ROLLBACK_COOKIE, workspace_id, httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE, path='/',
    )


def _workspace(request, response, create=False):
    workspace_id = request.cookies.get(ROLLBACK_COOKIE)
    try:
        if workspace_id:
            rollback_storage.load_state(workspace_id)
            return workspace_id
    except HTTPException as exc:
        if exc.status_code != 404:
            raise
    if not create:
        return None
    workspace_id = rollback_storage.create_workspace()
    _set_cookie(response, workspace_id)
    return workspace_id


@router.get('/workspace')
def get_rollback_workspace(request: Request, response: Response):
    workspace_id = _workspace(request, response)
    if not workspace_id:
        return {'school': None, 'file': None, 'dump': None}
    state = rollback_storage.load_state(workspace_id)
    result = {'school': state.get('school'), 'file': None, 'dump': None}
    if isinstance(state.get('input'), dict):
        metadata, data = rollback_storage.read_input(workspace_id)
        result['file'] = preview_file(metadata.get('name', ''), data, metadata.get('sheet'))
    if isinstance(state.get('dump'), dict):
        result['dump'] = rollback_storage.read_dump_page(
            workspace_id, 1, DUMP_PREVIEW_PAGE_SIZE,
        )
    return result

@router.post('/school')
def set_rollback_school(payload: SchoolInput, request: Request, response: Response):
    school = get_school(payload.school_index)
    try:
        with stream_rollback_dump(school['school_index']) as (columns, rows):
            workspace_id = _workspace(request, response, create=True)
            rollback_storage.save_school_rows(workspace_id, school, columns, rows)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'Could not fetch the rollback dump from the database.') from exc
    return {
        'school': school,
        'dump': rollback_storage.read_dump_page(workspace_id, 1, DUMP_PREVIEW_PAGE_SIZE),
    }


@router.delete('/school')
def clear_rollback_school(request: Request, response: Response):
    workspace_id = _workspace(request, response)
    if workspace_id:
        rollback_storage.clear_school(workspace_id)
    return {'school': None, 'dump': None}


@router.get('/dump/preview')
def preview_rollback_dump(request: Request, response: Response, page: int = 1):
    workspace_id = _workspace(request, response)
    if not workspace_id:
        raise HTTPException(409, 'Verify a school first.')
    return rollback_storage.read_dump_page(workspace_id, page, DUMP_PREVIEW_PAGE_SIZE)


@router.get('/dump/download')
def download_rollback_dump(
    request: Request, response: Response,
    file_format: Literal['csv', 'xlsx'] = 'csv',
):
    workspace_id = _workspace(request, response)
    if not workspace_id:
        raise HTTPException(409, 'Verify a school first.')
    state = rollback_storage.load_state(workspace_id)
    school = state.get('school')
    if not isinstance(school, dict) or not school.get('school_index'):
        raise HTTPException(409, 'Verify a school first.')
    try:
        exported = _export_dump_file(workspace_id, file_format)
    except (ValueError, IllegalCharacterError) as exc:
        raise HTTPException(
            400, 'Could not create the dump file. Download CSV or check for invalid spreadsheet characters.',
        ) from exc
    filename = f'rollback-dump-{school["school_index"]}.{file_format}'
    media_type = ('text/csv; charset=utf-8' if file_format == 'csv' else
                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    return FileResponse(
        exported, media_type=media_type, filename=filename,
        headers={'Cache-Control': 'no-store'},
        background=BackgroundTask(exported.unlink, missing_ok=True),
    )


@router.post('/files')
def upload_rollback_file(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    sheet: Annotated[str | None, Form()] = None,
):
    """Validate a browser-uploaded CSV/XLSX file and return its metadata."""
    try:
        data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise HTTPException(400, 'Could not read the uploaded file.') from exc
    result = preview_file(file.filename or '', data, sheet)
    workspace_id = _workspace(request, response, create=True)
    rollback_storage.save_input(
        workspace_id, {'name': file.filename or '', 'sheet': result['sheet']}, data,
    )
    return result


@router.get('/files/preview')
def preview_rollback_file(request: Request, response: Response, page: int = 1):
    workspace_id = _workspace(request, response)
    if not workspace_id:
        raise HTTPException(409, 'Upload a rollback file first.')
    metadata, data = rollback_storage.read_input(workspace_id)
    return preview_file(metadata.get('name', ''), data, metadata.get('sheet'), page)


@router.delete('/files')
def clear_rollback_file(request: Request, response: Response):
    workspace_id = _workspace(request, response)
    if workspace_id:
        rollback_storage.clear_input(workspace_id)
    return {'file': None}


@router.post('/files/sheet')
def select_rollback_sheet(payload: RollbackSheetInput, request: Request, response: Response):
    workspace_id = _workspace(request, response)
    if not workspace_id:
        raise HTTPException(409, 'Upload a rollback file first.')
    metadata, data = rollback_storage.read_input(workspace_id)
    result = preview_file(metadata.get('name', ''), data, payload.sheet)
    rollback_storage.update_input_metadata(
        workspace_id, {'name': metadata.get('name', ''), 'sheet': result['sheet']},
    )
    return result
