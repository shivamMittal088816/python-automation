"""Owner-scoped accepted-member listing."""
import logging
from typing import Literal
from app.api.session_cookie import require_session
from app.invitations.services.creation import _workspace_id
from app.invitations.access import member_access
from app.invitations.services.members import list_accepted_members
from app.routes.bulk_registration.workspace_access import workspace_for
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.config.dependencies import get_db

router = APIRouter()
logger = logging.getLogger('uvicorn.error')


@router.get('/members')
def accepted_members(request: Request, response: Response,
                     workflow: Literal['mapping', 'bulk_registration'], db: Session = Depends(get_db)):
    """List accepted invitees for the owner's current workspace; never expose credentials."""
    if member_access(request, workflow):
        raise HTTPException(403, 'Only the workspace owner can view invited members.')
    if workflow == 'mapping':
        workspace_id = _workspace_id(require_session(request, response))
    else:
        workspace_id, _ = workspace_for(request, response)
    response.headers['Cache-Control'] = 'no-store'
    try:
        return list_accepted_members(db, workspace_id, workflow)
    except SQLAlchemyError:
        logger.exception('Invitation member listing failed')
        raise HTTPException(503, 'Members are temporarily unavailable. Please try again shortly.')
