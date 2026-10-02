"""Check that workspace metadata still matches saved workflow data."""
from fastapi import HTTPException


def storage_available(record):
    if record.deleted_at:
        return False
    try:
        if record.workflow_type == 'mapping':
            from app.api.file_workflow_state import session_folder, _is_expired
            from app.api.file_workflow_session_storage import load_state
            folder = session_folder(record.storage_id)
            return not _is_expired(folder) and load_state(folder)['workspace_id'] == record.id
        from app.services.bulk_registration_storage import load_workspace
        return load_workspace(record.storage_id, touch=False)['workspace_id'] == record.id
    except HTTPException:
        return False
