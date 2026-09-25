"""Admission mapping endpoints for the mapping API."""
from Backend.api.session_cookie import SessionId, WorkspaceRevision
from fastapi import APIRouter
from Backend.api.file_workflow_state import workspace
from Backend.schemas.file_workflow import AdmissionRunInput
from Backend.services.admission_mapping.admission_file_mapping import map_students, build_exports
from Backend.api.file_workflow_configuration import admission_configuration
from Backend.api.file_workflow_validation import fail, require_dump_school_index
from Backend.api.file_workflow_snapshots import read_snapshot
from Backend.api.file_workflow_responses import summary
from Backend.api.file_workflow_invalidation import clear_email_and_class_mapping


router = APIRouter(tags=['Admission mapping'])


@router.post('/admission-mapping/run')
def admission_map(session_id: SessionId, revision: WorkspaceRevision, payload: AdmissionRunInput | None = None):
    with workspace(session_id, expected_revision=revision) as saved_state:
        state = dict(saved_state)
        state['admission_settings'] = dict(saved_state.get('admission_settings', {}))
        if payload:
            state['admission_settings'].update(payload.model_dump(exclude_unset=True))
        config=admission_configuration(state, apply_settings=True)
        if not config:
            fail('Add a school file and student dump first.')
        if config['missing_columns']:
            fail('Dump file is missing required columns: '+', '.join(config['missing_columns']))
        require_dump_school_index(state)
        values=state['admission_settings']
        try:
            result=map_students(read_snapshot(state['saved_admission_school'],values.get('admission_school_sheet')),
                read_snapshot(state['saved_admission_dump'],values.get('admission_dump_sheet')),
                values['school_admission_col'],config['dump_admission'],config['username'],values['school_name_col'],
                name_is_full=False,dump_first_name_column=config['dump_first_name'])
            state['admission_exports']=build_exports(result)
            clear_email_and_class_mapping(state)
        except (ValueError,KeyError,OSError) as exc:
            state.pop('admission_exports',None)
            fail(f'Could not map these files: {exc}')
        result = summary(state,session_id)
        saved_state.clear()
        saved_state.update(state)
        return result
