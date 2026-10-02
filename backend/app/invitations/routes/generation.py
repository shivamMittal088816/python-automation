"""Generate invitation links for the current owner's workspaces."""
import logging
from fastapi import status
from app.api.session_cookie import require_session
from app.api.file_workflow_state import create_session
from app.config.settings import settings
from app.invitations.schemas import CreateInvitationRequest, InvitationResponse
from app.invitations.services.creation import create_invitation, _workspace_id
from app.invitations.access import member_access
from app.workspaces.services.identity import user_id
from app.routes.bulk_registration.workspace_access import workspace_for
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.config.dependencies import get_db

router = APIRouter()
logger = logging.getLogger('uvicorn.error')


def _frontend_origin(request: Request) -> str:
    origin = request.headers.get('origin')
    if origin:
        return origin
    return next(value.strip() for value in settings.CORS_ORIGINS.split(',') if value.strip())


@router.post('', response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def generate_invitation(payload: CreateInvitationRequest, request: Request,
                        response: Response, db: Session = Depends(get_db)):
    user_id(request)
    workflows = ('mapping', 'bulk_registration') if payload.workflow == 'both' else (payload.workflow,)
    if any(member_access(request, workflow) for workflow in workflows):
        raise HTTPException(403, 'Only the workspace owner can create invitations.')
    session_id = None
    if payload.workflow != 'bulk_registration':
        try:
            session_id = require_session(request, response)
        except HTTPException as exc:
            if payload.workflow != 'both' or exc.status_code not in (401, 409):
                raise
            from app.workspaces.services.ownership import register_owned
            session_id = create_session(persistent=True)
            register_owned(request, response, 'mapping', _workspace_id(session_id), session_id)
    bulk_id = None
    if payload.workflow in ('bulk_registration', 'both'):
        bulk_id, _ = workspace_for(request, response, allow_create=True)
    try:
        return create_invitation(db, session_id, _frontend_origin(request), payload, bulk_id)
    except SQLAlchemyError:
        logger.exception('Invitation database write failed')
        raise HTTPException(503, 'Invitations are temporarily unavailable. Please try again shortly.')
