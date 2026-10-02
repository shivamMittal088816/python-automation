"""Verify ownership or live membership for the selected workspace."""
from fastapi import HTTPException
from sqlalchemy import select
from app.models.workflow_member_model import WorkflowMember
from app.workspaces.models import Workspace, WorkspacePreference
from app.workspaces.services.identity import database, user_id
from app.workspaces.services.memberships import member_status
from app.workspaces.services.storage import storage_available


def access_to(db, owner_id, record):
    if record is None:
        raise HTTPException(410, 'This workspace is unavailable. Select another workspace.')
    if record.deleted_at:
        raise HTTPException(410, {
            'code': 'workspace_removed',
            'message': 'The owner deleted this workspace. Select another workspace to continue.',
        })
    if record.owner_user_id == owner_id:
        role = 'owner'
    else:
        member = db.scalar(select(WorkflowMember).where(
            WorkflowMember.user_id == owner_id, WorkflowMember.workspace_id == record.id,
            WorkflowMember.workflow_type == record.workflow_type))
        if member is None or member_status(member) != 'active':
            raise HTTPException(403, 'Shared workflow access expired or was revoked. Select another workspace.')
        if member.role not in ('editor', 'viewer'):
            raise HTTPException(403, 'Shared workspace permissions are invalid. Ask the owner to update your access.')
        role = member.role
    if not storage_available(record):
        raise HTTPException(410, 'Workspace files are unavailable. Select or create another workspace.')
    return {'id': record.public_id, 'workspace_id': record.id, 'storage_id': record.storage_id,
            'role': role, 'name': record.name}


def selected_access(request, workflow, db=None):
    if getattr(request.state, 'auth_user', None) is None:
        return None
    session = database(request, db)
    selected = session.get(WorkspacePreference, (user_id(request), workflow))
    if selected is None:
        return None
    record = session.get(Workspace, selected.active_workspace_id)
    if record is None or record.workflow_type != workflow:
        raise HTTPException(410, 'The selected workspace is unavailable.')
    context_header = 'X-Mapping-Workspace' if workflow == 'mapping' else 'X-Bulk-Registration-Workspace'
    expected = request.headers.get(context_header) or request.headers.get('X-Active-Workspace')
    if expected and expected != record.public_id:
        raise HTTPException(409, 'The active workspace changed in another tab. Reload before continuing.',
                            headers={'X-Workspace-Selection-Conflict': '1'})
    return access_to(session, user_id(request), record)
