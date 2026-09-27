"""Workspace restoration, file clearing, and complete reset endpoints."""
from typing import Annotated

from fastapi import APIRouter, Header, Request, Response

from app.routes.bulk_registration.workspace_access import (
    require_revision, set_workspace_cookie, workspace_for, workspace_summary,
)
from app.services.bulk_registration_storage import create_workspace, delete_workspace, load_workspace, save_workspace, workspace_locked


router = APIRouter()
Revision = Annotated[int, Header(alias='X-Workspace-Revision', ge=0)]


@router.get('/workspace')
@workspace_locked
def get_workspace(request: Request, response: Response):
    _, state = workspace_for(request, response)
    return workspace_summary(state)


@router.post('/workspace')
@workspace_locked
def initialize_workspace(request: Request, response: Response):
    _, state = workspace_for(request, response, allow_create=True)
    return workspace_summary(state)


@router.delete('/file')
@workspace_locked
def clear_file(request: Request, response: Response, expected_revision: Revision):
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    state.update({'file': None, 'path': '', 'output': None, 'outputs': {},
                  'revision': expected_revision + 1})
    state.pop('input', None)
    save_workspace(workspace_id, state)
    return workspace_summary(state)


@router.delete('/workspace')
@workspace_locked
def reset_workspace(request: Request, response: Response, expected_revision: Revision):
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    delete_workspace(workspace_id)
    new_id = create_workspace()
    set_workspace_cookie(response, new_id)
    return workspace_summary(load_workspace(new_id))
