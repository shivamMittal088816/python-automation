"""Create additional personal workspaces."""
from app.api.file_workflow_state import create_session, session_folder
from app.api.file_workflow_session_storage import load_state
from app.services.bulk_registration_storage import create_workspace
from app.workspaces.schemas import CreateWorkspaceRequest
from app.workspaces.services.identity import user_id
from app.workspaces.services.ownership import register_owned
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.config.dependencies import get_db

router = APIRouter()


@router.post('', status_code=201)
def create_owned_workspace(payload: CreateWorkspaceRequest, request: Request, response: Response,
                           db: Session = Depends(get_db)):
    user_id(request)
    if payload.workflow == 'mapping':
        storage_id = create_session(persistent=True)
        workspace_id = load_state(session_folder(storage_id))['workspace_id']
    else:
        storage_id = workspace_id = create_workspace(persistent=True)
    record = register_owned(request, response, payload.workflow, workspace_id, storage_id, db)
    return {'active_workspace_id': record.public_id}
