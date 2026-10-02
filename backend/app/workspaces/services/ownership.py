"""Register newly created workspaces and select them for their owner."""
from sqlalchemy import func, select
from app.common.time import now
from app.workspaces.models import Workspace
from app.workspaces.services.identity import database, public_id, user_id
from app.workspaces.services.preferences import lock_user, preference


def register_owned(request, response, workflow, workspace_id, storage_id, db=None):
    session = database(request, db)
    owner_id = user_id(request)
    lock_user(session, owner_id)
    count = session.scalar(select(func.count()).select_from(Workspace).where(
        Workspace.owner_user_id == owner_id, Workspace.workflow_type == workflow))
    record = Workspace(id=workspace_id, public_id=public_id(workflow, workspace_id),
                       name='My workspace' if count == 0 else f'My workspace {count + 1}',
                       workflow_type=workflow, owner_user_id=owner_id, storage_id=storage_id, created_at=now())
    session.add(record)
    session.flush()
    preference(session, owner_id, workflow, workspace_id)
    session.commit()
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Active-Workspace'] = record.public_id
    return record
