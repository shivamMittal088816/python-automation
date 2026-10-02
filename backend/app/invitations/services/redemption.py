"""Atomically redeem invitations into account memberships and preferences."""
from datetime import datetime, timezone
import hashlib
from fastapi import HTTPException
from sqlalchemy import select
from app.models.workflow_invitation_model import WorkflowInvitation
from app.models.workflow_member_model import WorkflowMember
from app.workspaces.models import Workspace
from app.workspaces.services.identity import user_id
from app.workspaces.services.memberships import member_status
from app.workspaces.services.storage import storage_available
from app.workspaces.services.preferences import lock_user, preference


def redeem_invitation(db, token, request):
    """Consume a single-use invite, bind membership to the account and select it atomically."""
    try:
        owner_id = user_id(request)
        invitation = db.scalar(select(WorkflowInvitation).where(
            WorkflowInvitation.token_hash == hashlib.sha256(token.encode()).digest(),
        ).with_for_update())
        if invitation is None:
            raise HTTPException(404, 'Invitation code was not found. Check the code and try again.')
        if invitation.revoked_at is not None:
            raise HTTPException(410, 'This invitation was revoked. Ask for a new code.')
        if invitation.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
            raise HTTPException(410, 'This invitation expired. Ask for a new code.')
        if invitation.max_uses is not None and invitation.use_count >= invitation.max_uses:
            raise HTTPException(409, 'This invitation has already been used. Ask for a new code.')
        targets = {}
        if invitation.workflow_type in ('mapping', 'both'):
            targets['mapping'] = invitation.workspace_id
        if invitation.workflow_type in ('bulk_registration', 'both'):
            targets['bulk_registration'] = (invitation.bulk_workspace_id
                if invitation.workflow_type == 'both' else invitation.workspace_id)
        lock_user(db, owner_id)
        previous = {}
        for workflow, workspace_id in targets.items():
            record = db.get(Workspace, workspace_id) if workspace_id else None
            if record is None or record.workflow_type != workflow or not storage_available(record):
                raise HTTPException(410, 'The shared workspace is unavailable. Ask for a new code.')
            if record.owner_user_id == owner_id:
                raise HTTPException(409, 'You cannot accept an invitation to your own workspace.')
            member = db.scalar(select(WorkflowMember).where(
                WorkflowMember.user_id == owner_id, WorkflowMember.workspace_id == workspace_id,
                WorkflowMember.workflow_type == workflow).with_for_update())
            if member is not None and member_status(member) == 'active':
                raise HTTPException(409, 'You already have access to this shared workspace.')
            previous[workflow] = member
        for workflow, workspace_id in targets.items():
            member = previous[workflow]
            if member is None:
                member = WorkflowMember(user_id=owner_id, workflow_type=workflow,
                                        workspace_id=workspace_id, joined_at=datetime.now(timezone.utc).replace(tzinfo=None))
                db.add(member)
            member.role = invitation.permission
            member.invitation_id = invitation.id
            member.revoked_at = None
            member.expires_at = None
            member.member_token_hash = None
            preference(db, owner_id, workflow, workspace_id)
        invitation.use_count += 1
        result = {'destination': '/bulk-reg' if invitation.workflow_type == 'bulk_registration' else '/admission_file_page',
                  'permission': invitation.permission, 'workflow': invitation.workflow_type}
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
