"""Full name and class mapping endpoints for the mapping API."""
from Backend.api.session_cookie import SessionId
import hashlib
from fastapi import APIRouter
from Backend.api.file_workflow_state import workspace
from Backend.schemas.file_workflow import FullNameInput
from Backend.services.email_mapping.email_file_mapping import email_school_input, sync_email_stage
from Backend.services.full_name_class_mapping.full_name_class_file_mapping import map_by_full_name_class, read_saved_dump
from Backend.services.full_name_class_mapping.full_name_class_second_round import map_second_round
from Backend.services.shared_mapping.mapping_account_uniqueness import review_duplicate_accounts
from Backend.api.file_workflow_constants import SOURCES
from Backend.api.file_workflow_validation import fail, require_dump_school_index
from Backend.api.file_workflow_snapshots import read_snapshot
from Backend.api.file_workflow_responses import summary


router = APIRouter(tags=['Full name and class mapping'])


@router.post('/full-name-class-mapping/run')
def full_name_map(session_id: SessionId,payload: FullNameInput):
    with workspace(session_id) as state:
        require_dump_school_index(state)
        sync_email_stage(state)
        field,filename=SOURCES[payload.source]
        source=state.get(field,{}).get(filename)
        if not source:
            fail(f'{payload.source} is not available yet. Choose the other file or complete this mapping first.')
        if not state.get('saved_admission_dump'):
            fail('Load the admission dump first.')
        school=email_school_input(read_snapshot({'name':filename,'data':source['data']}))
        dump=read_saved_dump(state['saved_admission_dump'],state.get('admission_settings',{}).get('admission_dump_sheet'))
        if 'generated_col' not in dump:
            fail('The admission dump has no generated_col column.')
        if school.empty:
            fail('No students in this file.')
        if payload.name_column not in school or payload.class_column not in school:
            fail('Choose the full name and Class Number columns.')
        signature=(payload.source,hashlib.sha256(source['data']).hexdigest(),
            hashlib.sha256(state['saved_admission_dump']['data']).hexdigest(),payload.name_column,payload.class_column,'account_unique_all_dump_rows_v5')
        if payload.round == 2:
            previous_signature=tuple(state.get('full_name_class_result_signature') or ())
            if previous_signature[:3] != signature[:3] or previous_signature[5:6] != signature[5:6] or not state.get('full_name_class_exports'):
                fail('Run 1st round mapping for this input file first.')
            if 'fullname' not in dump or 'user_edu_class' not in dump:
                fail('The dump must contain fullname and user_edu_class columns for round 2.')
            first_round=state.get('full_name_class_round_one_exports')
            if not first_round and len(previous_signature) == 6:
                first_round=dict(state['full_name_class_exports'])
            if not first_round:
                fail('Run 1st round mapping again before starting round 2.')
            result=map_second_round(first_round,dump,payload.name_column,payload.class_column)
            state['full_name_class_round_one_exports']=first_round
            signature=previous_signature[:6]+('sorted_characters_round_2_v2',payload.name_column,payload.class_column)
        else:
            result=map_by_full_name_class(school,dump,payload.name_column,payload.class_column)
        values=state.setdefault('admission_settings',{})
        if payload.round == 2:
            values.update(full_name_class_round_two_name_column=payload.name_column,
                          full_name_class_round_two_class_column=payload.class_column)
        else:
            values.update(full_name_class_name_column=payload.name_column,full_name_class_class_column=payload.class_column,full_name_class_source=payload.source)
        state['full_name_class_exports']=result
        state['full_name_class_result_signature']=signature
        review_duplicate_accounts(state)
        if payload.round == 1:
            state['full_name_class_round_one_exports']=dict(state['full_name_class_exports'])
        return summary(state,session_id)
