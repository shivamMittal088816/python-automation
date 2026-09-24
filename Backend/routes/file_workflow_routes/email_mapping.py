"""Email mapping endpoints for the mapping API."""
from Backend.api.session_cookie import SessionId
import logging
from fastapi import APIRouter
from Backend.api.file_workflow_state import workspace
from Backend.schemas.file_workflow import EmailInput, EmailSecondPassInput
from Backend.repositories.email_dump_service import fetch_email_dump
from Backend.services.email_mapping.email_file_mapping import email_school_input, sync_email_stage
from Backend.services.email_mapping.email_file_mapping import map_by_email
from Backend.services.email_mapping.email_input import email_pass_one_complete
from Backend.services.shared_mapping.mapping_account_uniqueness import review_duplicate_accounts
from Backend.api.file_workflow_validation import fail, require_dump_school_index
from Backend.api.file_workflow_snapshots import read_snapshot
from Backend.api.file_workflow_responses import summary


router = APIRouter(tags=['Email mapping'])
logger = logging.getLogger('uvicorn.error')


@router.post('/email-mapping/run')
def email_map(session_id: SessionId,payload: EmailInput):
    with workspace(session_id) as state:
        require_dump_school_index(state)
        if not sync_email_stage(state):
            fail('Complete admission mapping with Not matched students first.')
        school=email_school_input(read_snapshot({'name':'source.xlsx','data':state['admission_exports']['not_matched.xlsx']['data']}))
        if payload.email_column not in school or payload.name_column not in school:
            fail('Choose the school email and first name columns.')
        values=state.setdefault('admission_settings',{})
        school_index=state.get('saved_admission_dump',{}).get('school_index')
        try:
            dump=fetch_email_dump(school[payload.email_column])
            result=map_by_email(school,dump,payload.email_column,'user_email',payload.name_column,school_index=school_index)
        except Exception:
            logger.exception('Failed to fetch or map the email dump.')
            fail('Could not fetch or map the email dump. Check the database connection and try again.',503)
        values.update(email_input_column=payload.email_column,email_first_name_column=payload.name_column)
        state['saved_email_dump']={'name':'email_dump.csv','data':dump.to_csv(index=False).encode('utf-8')}
        state['email_exports']=result
        values['email_result_pass'] = 1
        state['email_result_signature']=(state['email_source_signature'],payload.email_column,payload.name_column,'email_first_name_school_v12',school_index)
        state.pop('full_name_class_exports',None)
        state.pop('full_name_class_round_one_exports',None)
        state.pop('full_name_class_result_signature',None)
        review_duplicate_accounts(state)
        return summary(state,session_id)



@router.post('/email-mapping/second-pass')
def email_second_pass(session_id: SessionId, payload: EmailSecondPassInput):
    from Backend.services.email_mapping.email_second_pass import map_email_second_pass

    with workspace(session_id) as state:
        require_dump_school_index(state)
        sync_email_stage(state)
        if not email_pass_one_complete(state):
            fail('Run email mapping pass 1 successfully for the current files and selected columns before pass 2.')
        signature = state['email_result_signature']
        source = email_school_input(read_snapshot({'name':'source.xlsx','data':state['admission_exports']['not_matched.xlsx']['data']}))
        if payload.name_column not in source:
            fail('Choose the school full name column for email pass 2.')
        try:
            result = map_email_second_pass(state['email_exports'], read_snapshot(state['saved_email_dump']),
                signature[1], payload.name_column, state['saved_admission_dump']['school_index'])
        except (ValueError, KeyError) as exc:
            fail(str(exc))
        state['email_exports'] = result
        state['admission_settings']['email_full_name_column'] = payload.name_column
        state['admission_settings']['email_result_pass'] = 2
        review_duplicate_accounts(state)
        return summary(state, session_id)
