"""Rollback input upload, preview, worksheet, and sanity-check routes."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel

from app.config.settings import settings
from app.routes.rollback.access import workspace_for
from app.services import rollback as rollback_storage
from app.services.rollback.header_validation import validate_rollback_headers
from app.services.tabular_file import preview_file


router = APIRouter(prefix='/files')


class RollbackSheetInput(BaseModel):
    sheet: str


@router.post('')
def upload_rollback_file(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    sheet: Annotated[str | None, Form()] = None,
):
    try:
        data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise HTTPException(400, 'Could not read the uploaded file.') from exc
    result = preview_file(file.filename or '', data, sheet)
    workspace_id = workspace_for(request, response, create=True)
    rollback_storage.save_input(
        workspace_id,
        {
            'name': file.filename or '',
            'sheet': result['sheet'],
            'columns': result['columns'],
        },
        data,
    )
    return result


@router.get('/preview')
def preview_rollback_file(request: Request, response: Response, page: int = 1):
    workspace_id = workspace_for(request, response)
    if not workspace_id:
        raise HTTPException(409, 'Upload a rollback file first.')
    metadata, data = rollback_storage.read_input(workspace_id)
    return preview_file(metadata.get('name', ''), data, metadata.get('sheet'), page)


@router.post('/sanity-check')
def sanity_check_rollback_file(request: Request, response: Response):
    workspace_id = workspace_for(request, response)
    if not workspace_id:
        raise HTTPException(409, 'Upload a rollback file first.')
    metadata, data = rollback_storage.read_input(workspace_id)
    columns = metadata.get('columns')
    if not isinstance(columns, list) or not all(isinstance(column, str) for column in columns):
        preview = preview_file(metadata.get('name', ''), data, metadata.get('sheet'))
        columns = preview['columns']
        rollback_storage.update_input_metadata(
            workspace_id,
            {**metadata, 'columns': columns},
        )
    return validate_rollback_headers(columns)


@router.delete('')
def clear_rollback_file(request: Request, response: Response):
    workspace_id = workspace_for(request, response)
    if workspace_id:
        rollback_storage.clear_input(workspace_id)
    return {'file': None}


@router.post('/sheet')
def select_rollback_sheet(
    payload: RollbackSheetInput,
    request: Request,
    response: Response,
):
    workspace_id = workspace_for(request, response)
    if not workspace_id:
        raise HTTPException(409, 'Upload a rollback file first.')
    metadata, data = rollback_storage.read_input(workspace_id)
    result = preview_file(metadata.get('name', ''), data, payload.sheet)
    rollback_storage.update_input_metadata(
        workspace_id,
        {
            'name': metadata.get('name', ''),
            'sheet': result['sheet'],
            'columns': result['columns'],
        },
    )
    return result
