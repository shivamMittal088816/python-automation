"""Admission mapping endpoints for the mapping API."""
from Backend.api.session_cookie import SessionId
from fastapi import APIRouter
from Backend.api.file_workflow_state import workspace
from Backend.schemas.file_workflow import MoveInput, AdmissionSecondPassInput, AdmissionRunInput
from Backend.services.admission_mapping.admission_file_mapping import map_students, build_exports
from Backend.api.file_workflow_configuration import admission_configuration
from Backend.api.file_workflow_validation import fail, require_dump_school_index
from Backend.api.file_workflow_snapshots import read_snapshot
from Backend.api.file_workflow_responses import summary


router = APIRouter(tags=['Admission mapping'])


@router.post('/admission-mapping/run')
def admission_map(session_id: SessionId, payload: AdmissionRunInput | None = None):
    with workspace(session_id) as saved_state:
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
            values['admission_result_pass'] = 1
        except (ValueError,KeyError,OSError) as exc:
            state.pop('admission_exports',None)
            fail(f'Could not map these files: {exc}')
        for key in ('email_exports','email_result_signature','full_name_class_exports','full_name_class_result_signature','full_name_class_round_one_exports'):
            state.pop(key,None)
        result = summary(state,session_id)
        saved_state.clear()
        saved_state.update(state)
        return result


@router.post('/admission-mapping/move')
def admission_move(session_id: SessionId,payload: MoveInput):
    fail('Student previews are locked. Moving students between result groups is disabled.',403)



@router.post('/admission-mapping/second-pass')
def admission_second_pass(session_id: SessionId, payload: AdmissionSecondPassInput):
    from Backend.services.admission_mapping.admission_second_pass import map_admission_second_pass
    from Backend.services.shared_mapping.mapping_account_uniqueness import review_duplicate_accounts

    with workspace(session_id) as state:
        config = admission_configuration(state, apply_settings=True)
        require_dump_school_index(state)
        if not config or config['missing_columns'] or not all(
                name in state.get('admission_exports', {}) for name in ('matched.xlsx', 'review.xlsx', 'not_matched.xlsx')):
            fail('Run admission mapping pass 1 for the current files and columns before pass 2.')
        if payload.name_column not in config['school_columns']:
            fail('Choose the full name column from the school input file.')
        values = state['admission_settings']
        try:
            result = map_admission_second_pass(state['admission_exports'],
                read_snapshot(state['saved_admission_dump'], values.get('admission_dump_sheet')),
                payload.name_column, config['dump_admission'], config['username'])
        except (ValueError, KeyError) as exc:
            fail(str(exc))
        state['admission_exports'] = result
        values['admission_round_two_name_column'] = payload.name_column
        values['admission_result_pass'] = 2
        review_duplicate_accounts(state)
        return summary(state, session_id)
