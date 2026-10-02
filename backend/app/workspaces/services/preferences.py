"""Persist account selections with a per-user database lock."""
from sqlalchemy import select
from app.auth.models import User
from app.common.time import now
from app.workspaces.models import WorkspacePreference


def lock_user(db, owner_id):
    return db.scalar(select(User).where(User.id == owner_id).with_for_update())


def preference(db, owner_id, workflow, workspace_id):
    # Callers lock the user row first, including when this preference is absent.
    record = db.get(WorkspacePreference, (owner_id, workflow))
    if record is None:
        record = WorkspacePreference(user_id=owner_id, workflow_type=workflow,
                                     active_workspace_id=workspace_id, updated_at=now())
        db.add(record)
    else:
        record.active_workspace_id = workspace_id
        record.updated_at = now()
