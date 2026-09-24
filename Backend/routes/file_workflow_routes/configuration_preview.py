"""Preview mapping configuration using draft settings."""
from Backend.api.session_cookie import SessionId
from fastapi import APIRouter
from Backend.api.file_workflow_state import workspace
from Backend.schemas.file_workflow import AdmissionRunInput
from Backend.api.file_workflow_configuration import admission_configuration


router = APIRouter(tags=['Mapping sessions'])


@router.post('/configuration-preview')
def configuration_preview(session_id: SessionId, payload: AdmissionRunInput):
    with workspace(session_id, persist=False) as saved:
        state = dict(saved)
        state['admission_settings'] = dict(saved.get('admission_settings', {}))
        state['admission_settings'].update(payload.model_dump(exclude_unset=True))
        config = admission_configuration(state)
        return {'configuration': config, 'settings': state['admission_settings']}
