"""Soft-delete an owned workspace while retaining its files and related records."""
from fastapi import HTTPException
from sqlalchemy import select

from app.common.time import now
from app.workspaces.models import Workspace, WorkspacePreference
from app.workspaces.services.preferences import lock_user
from app.workspaces.services.storage import storage_available


def soft_delete_workspace(db, owner_id, workspace_id):
    try:
        lock_user(db, owner_id)
        record = db.scalar(select(Workspace).where(
            Workspace.public_id == workspace_id).with_for_update())
        if record is None:
            raise HTTPException(404, 'Workspace not found.')
        if record.owner_user_id != owner_id:
            raise HTTPException(403, 'Only the workspace owner can delete it.')
        # Repeated requests preserve the original retention start time.
        if record.deleted_at is None:
            record.deleted_at = now()
        selected = db.get(WorkspacePreference, (owner_id, record.workflow_type))
        if selected and selected.active_workspace_id == record.id:
            alternatives = db.scalars(select(Workspace).where(
                Workspace.owner_user_id == owner_id,
                Workspace.workflow_type == record.workflow_type,
                Workspace.deleted_at.is_(None), Workspace.id != record.id)
                .order_by(Workspace.created_at, Workspace.id)).all()
            replacement = next((item for item in alternatives if storage_available(item)), None)
            if replacement:
                selected.active_workspace_id = replacement.id
                selected.updated_at = now()
            else:
                db.delete(selected)
                selected = None
        active = db.get(Workspace, selected.active_workspace_id) if selected else None
        result = {'id': record.public_id, 'deleted_at': record.deleted_at,
                  'active_workspace_id': active.public_id if active and active.deleted_at is None else None}
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
