"""File intake endpoints for the rollback workflow."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel

from app.config.settings import settings
from app.routes.bulk_registration.file_reading import preview_file
from app.routes.bulk_registration.models import SchoolInput
from app.routes.bulk_registration.school_routes import get_school
from app.services import rollback_storage


router = APIRouter(prefix='/rollback')
ROLLBACK_COOKIE = '__Host-rollback-workspace' if settings.SESSION_COOKIE_SECURE else 'rollback_workspace'


class RollbackSheetInput(BaseModel):
    sheet: str


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
        return {'school': None, 'file': None}
    state = rollback_storage.load_state(workspace_id)
    result = {'school': state.get('school'), 'file': None}
    if isinstance(state.get('input'), dict):
        metadata, data = rollback_storage.read_input(workspace_id)
        result['file'] = preview_file(metadata.get('name', ''), data, metadata.get('sheet'))
    return result

@router.post('/school')
def set_rollback_school(payload: SchoolInput, request: Request, response: Response):
    school = get_school(payload.school_index)
    workspace_id = _workspace(request, response, create=True)
    rollback_storage.save_school(workspace_id, school)
    return {'school': school}


@router.delete('/school')
def clear_rollback_school(request: Request, response: Response):
    workspace_id = _workspace(request, response)
    if workspace_id:
        rollback_storage.clear_school(workspace_id)
    return {'school': None}


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
