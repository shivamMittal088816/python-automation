"""Generate single-use invitation credentials for selected workspaces."""
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from fastapi import HTTPException
from app.api.file_workflow_session_storage import load_state
from app.api.file_workflow_state import session_folder
from app.models.workflow_invitation_model import WorkflowInvitation
from app.invitations.repositories.invitations import save_invitation
from app.invitations.schemas import CreateInvitationRequest, InvitationResponse

INVITATION_LIFETIME = timedelta(hours=72)


def _workspace_id(session_id: str) -> str:
    state = load_state(session_folder(session_id))
    workspace_id = state.get('workspace_id')
    if not workspace_id:
        raise HTTPException(409, 'The current workspace cannot be shared yet.')
    return str(workspace_id)


def _destination(payload: CreateInvitationRequest) -> str:
    if payload.workflow == 'bulk_registration':
        return '/i/b'
    return '/i'


def create_invitation(db, session_id: str, frontend_origin: str,
                      payload: CreateInvitationRequest, bulk_workspace_id=None) -> InvitationResponse:
    """Create an opaque invitation; only its SHA-256 digest is persisted."""
    destination = _destination(payload)
    # 128 bits of randomness encode to a compact 22-character URL-safe token.
    token = secrets.token_urlsafe(16)
    expires_at = datetime.now(timezone.utc) + INVITATION_LIFETIME
    invitation = WorkflowInvitation(
        token_hash=hashlib.sha256(token.encode('utf-8')).digest(),
        workflow_type=payload.workflow,
        workspace_id=bulk_workspace_id if payload.workflow == 'bulk_registration' else _workspace_id(session_id),
        bulk_workspace_id=bulk_workspace_id if payload.workflow == 'both' else None,
        permission=payload.permission,
        expires_at=expires_at.replace(tzinfo=None),
        max_uses=1,
    )
    save_invitation(db, invitation)
    return InvitationResponse(
        invitation_url=f"{frontend_origin.rstrip('/')}{destination}/{token}",
        expires_at=expires_at,
    )
