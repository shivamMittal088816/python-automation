"""Preview mapping configuration using draft settings."""
from app.api.session_cookie import SessionId
from fastapi import APIRouter
from app.api.file_workflow_state import workspace
from app.schemas.file_workflow import AdmissionRunInput
from app.api.file_workflow_configuration import admission_configuration
from app.api.file_workflow_validation import fail


router = APIRouter(tags=['Mapping sessions'])


@router.post('/configuration-preview')
def configuration_preview(session_id: SessionId, payload: AdmissionRunInput):
    with workspace(session_id, persist=False) as saved:
        state = dict(saved)
        state['admission_settings'] = dict(saved.get('admission_settings', {}))
        state['admission_settings'].update(payload.model_dump(exclude_unset=True))
        try:
            config = admission_configuration(state)
        except (ValueError, KeyError, OSError):
            fail('Could not preview this configuration. Check the selected files, sheets, and columns.')
        return {'configuration': config, 'settings': state['admission_settings']}
