"""List the account's personal and joined workspaces."""
from sqlalchemy import select
from sqlalchemy.orm import load_only
from app.auth.models import User
from app.models.workflow_member_model import WorkflowMember
from app.workspaces.models import Workspace, WorkspacePreference
from app.workspaces.services.memberships import member_status
from app.workspaces.services.storage import storage_available


def list_account_workspaces(db, owner_id, workflow):
    owned = db.scalars(select(Workspace).where(Workspace.owner_user_id == owner_id,
        Workspace.workflow_type == workflow, Workspace.deleted_at.is_(None))
        .order_by(Workspace.created_at, Workspace.id)).all()
    joined = db.execute(select(Workspace, WorkflowMember, User).select_from(Workspace).join(WorkflowMember,
        (WorkflowMember.workspace_id == Workspace.id) & (WorkflowMember.workflow_type == Workspace.workflow_type))
        .join(User, Workspace.owner_user_id == User.id).options(load_only(User.id, User.name, User.email))
        .where(WorkflowMember.user_id == owner_id, Workspace.workflow_type == workflow)
        .order_by(WorkflowMember.joined_at.desc(), WorkflowMember.id.desc())).all()
    results = [{'id': item.public_id, 'name': item.name, 'needs_name': not item.name_confirmed, 'role': 'owner', 'workflow': workflow,
                'status': 'active' if storage_available(item) else 'unavailable', 'owned': True} for item in owned]
    for item, member, person in joined:
        status = member_status(member)
        if status == 'active' and not storage_available(item):
            status = 'unavailable'
        results.append({'id': item.public_id, 'name': f'{person.name} · {item.name}',
                        'role': member.role, 'workflow': workflow, 'status': status, 'owned': False,
                        'workspace_name': item.name, 'owner_name': person.name, 'owner_email': person.email})
    active = db.get(WorkspacePreference, (owner_id, workflow))
    selected = db.get(Workspace, active.active_workspace_id) if active else None
    return {'active_workspace_id': selected.public_id if selected else None, 'workspaces': results}
