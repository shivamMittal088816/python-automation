"""Upload, local-path, and worksheet-selection endpoints."""
from typing import Annotated

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, Response, UploadFile

from app.config.settings import settings
from app.routes.bulk_registration.file_reading import preview_file, read_path, read_frame
from app.services.bulk_registration_sanity import check_input
from app.services.bulk_registration_sanity.trimmed_file import trim_input_file
from app.routes.bulk_registration.models import FilePathInput, StoredFileInput
from app.routes.bulk_registration.workspace_access import require_revision, workspace_for, workspace_summary
from app.services.bulk_registration_storage import read_snapshot, save_workspace, workspace_locked


router = APIRouter()
Revision = Annotated[int, Header(alias='X-Workspace-Revision', ge=0)]


@router.post('/files/sanity-check')
@workspace_locked
def sanity_check(request: Request, response: Response, expected_revision: Revision):
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    if not state.get('input'):
        raise HTTPException(409, 'Load an input file first.')
    metadata, data = read_snapshot(workspace_id, state['input'])
    return check_input(read_frame(metadata.get('name', ''), data, metadata.get('sheet')))


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
    preview_file(file.filename or '', data, sheet)
    data = trim_input_file(file.filename or '', data)
    result = preview_file(file.filename or '', data, sheet)
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    state.update({'file': result, 'path': '', 'output': None, 'outputs': {}, 'output_verified': False,
                  'revision': expected_revision + 1})
    save_workspace(workspace_id, state, {'input': ({'name': file.filename or '', 'sheet': result['sheet']}, data)})
    return workspace_summary(state)


@router.post('/files/path')
@workspace_locked
def load_workspace_path(payload: FilePathInput, request: Request, response: Response,
                        expected_revision: Revision):
    name, data = read_path(payload.path)
    preview_file(name, data, payload.sheet)
    data = trim_input_file(name, data)
    result = preview_file(name, data, payload.sheet)
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    state.update({'file': result, 'path': payload.path, 'output': None, 'outputs': {}, 'output_verified': False,
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

# Purpose: Upload, local-path, and worksheet-selection endpoints.
# Its public interface includes get_input_page, upload_workspace_file, load_workspace_path, load_stored_file.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.__init__.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
