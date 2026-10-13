"""Rollback workspace restoration routes."""

from fastapi import APIRouter, Request, Response

from app.routes.rollback.access import workspace_for
from app.routes.rollback.constants import DUMP_PREVIEW_PAGE_SIZE
from app.services import rollback as rollback_storage
from app.services.tabular_file import preview_file


router = APIRouter()


@router.get('/workspace')
def get_rollback_workspace(request: Request, response: Response):
    workspace_id = workspace_for(request, response)
    if not workspace_id:
        return {'school': None, 'file': None, 'dump': None}
    state = rollback_storage.load_state(workspace_id)
    result = {'school': state.get('school'), 'file': None, 'dump': None}
    if isinstance(state.get('input'), dict):
        metadata, data = rollback_storage.read_input(workspace_id)
        result['file'] = preview_file(
            metadata.get('name', ''), data, metadata.get('sheet'),
        )
    if isinstance(state.get('dump'), dict):
        result['dump'] = rollback_storage.read_dump_page(
            workspace_id, 1, DUMP_PREVIEW_PAGE_SIZE,
        )
    return result
