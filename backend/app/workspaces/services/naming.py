"""Update workspace display names without changing identity, files or selection."""
from fastapi import HTTPException
from sqlalchemy import select

from app.workspaces.models import Workspace


def rename_workspace(db, owner_id, workspace_id, name):
    record = db.scalar(select(Workspace).where(
        Workspace.public_id == workspace_id, Workspace.deleted_at.is_(None)).with_for_update())
    if record is None:
        raise HTTPException(404, 'Workspace not found.')
    if record.owner_user_id != owner_id:
        raise HTTPException(403, 'Only the workspace owner can change its name.')
    record.name = name
    record.name_confirmed = True
    db.commit()
    return {'id': record.public_id, 'name': record.name, 'needs_name': False}
