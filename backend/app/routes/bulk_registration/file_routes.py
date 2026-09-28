"""Upload, local-path, and worksheet-selection endpoints."""
from typing import Annotated

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, Response, UploadFile

from app.config.settings import settings
from app.routes.bulk_registration.file_reading import preview_file, read_path
from app.routes.bulk_registration.models import FilePathInput, StoredFileInput
from app.routes.bulk_registration.workspace_access import require_revision, workspace_for, workspace_summary
from app.services.bulk_registration_storage import read_snapshot, save_workspace, workspace_locked


router = APIRouter()
Revision = Annotated[int, Header(alias='X-Workspace-Revision', ge=0)]


@router.get('/files/input')
@workspace_locked
def get_input_page(request: Request, response: Response, page: int = 1):
    workspace_id, state = workspace_for(request, response)
    if not state.get('input'):
        raise HTTPException(409, 'Load an input file first.')
    metadata, data = read_snapshot(workspace_id, state['input'])
    visible_state = dict(state)
    visible_state['file'] = preview_file(
        metadata.get('name', ''), data, metadata.get('sheet'), page,
    )
    return workspace_summary(visible_state)


@router.post('/files')
@workspace_locked
def upload_workspace_file(request: Request, response: Response, expected_revision: Revision,
                          file: UploadFile = File(...), sheet: Annotated[str | None, Form()] = None):
    try:
        data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise HTTPException(400, 'Could not read the uploaded file.') from exc
    result = preview_file(file.filename or '', data, sheet)
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    state.update({'file': result, 'path': '', 'output': None, 'outputs': {},
                  'revision': expected_revision + 1})
    save_workspace(workspace_id, state, {'input': ({'name': file.filename or '', 'sheet': result['sheet']}, data)})
    return workspace_summary(state)


@router.post('/files/path')
@workspace_locked
def load_workspace_path(payload: FilePathInput, request: Request, response: Response,
                        expected_revision: Revision):
    name, data = read_path(payload.path)
    result = preview_file(name, data, payload.sheet)
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    state.update({'file': result, 'path': payload.path, 'output': None, 'outputs': {},
                  'revision': expected_revision + 1})
    metadata = {'name': name, 'sheet': result['sheet'], 'source_path': payload.path}
    save_workspace(workspace_id, state, {'input': (metadata, data)})
    return workspace_summary(state)


@router.post('/files/stored')
@workspace_locked
def load_stored_file(payload: StoredFileInput, request: Request, response: Response,
                     expected_revision: Revision):
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    metadata, data = read_snapshot(workspace_id, state.get('input'))
    result = preview_file(metadata.get('name', ''), data, payload.sheet)
    state.update({'file': result,
                  'revision': expected_revision + 1})
    state['input']['metadata'] = metadata | {'sheet': result['sheet']}
    save_workspace(workspace_id, state)
    return workspace_summary(state)
