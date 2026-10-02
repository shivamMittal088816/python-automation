"""Validate access and update the user's active workspace."""
from sqlalchemy import select
from app.workspaces.models import Workspace
from app.workspaces.schemas import SelectWorkspaceRequest
from app.workspaces.services.identity import user_id
from app.workspaces.services.preferences import lock_user, preference
from app.workspaces.services.access import access_to
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.config.dependencies import get_db

router = APIRouter()


@router.post('/select')
def select_workspace(payload: SelectWorkspaceRequest, request: Request, response: Response,
                     db: Session = Depends(get_db)):
    owner_id = user_id(request)
    lock_user(db, owner_id)
    record = db.scalar(select(Workspace).where(Workspace.public_id == payload.workspace_id,
                                               Workspace.workflow_type == payload.workflow))
    if record is None:
        raise HTTPException(403, 'You do not have access to this workspace.')
    access = access_to(db, owner_id, record)
    preference(db, owner_id, payload.workflow, record.id)
    db.commit()
    response.headers['Cache-Control'] = 'no-store'
    return {'active_workspace_id': record.public_id, 'role': access['role']}
