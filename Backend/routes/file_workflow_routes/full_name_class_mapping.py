"""Full name and class mapping endpoints for the mapping API."""
from Backend.api.session_cookie import SessionId
import hashlib
from fastapi import APIRouter
from Backend.api.file_workflow_state import workspace
from Backend.schemas.file_workflow import FullNameInput
from Backend.services.full_name_class_mapping.full_name_class_file_mapping import map_by_full_name_class, read_saved_dump
from Backend.api.file_workflow_validation import fail
from Backend.api.file_workflow_snapshots import read_snapshot
from Backend.api.file_workflow_responses import summary


router = APIRouter(tags=['Full name and class mapping'])


@router.post('/full-name-class-mapping/run')
def full_name_map(session_id: SessionId,payload: FullNameInput):
    with workspace(session_id) as state:
        values=state.setdefault('admission_settings',{})
        sheet=None
        if payload.source == 'school_file':
            source=state.get('saved_admission_school')
            sheet=values.get('admission_school_sheet')
            if not source:
                fail('Load a school file first.')
        else:
            stage,filename,label = (
                ('admission_exports','not_matched.xlsx','Admission')
                if payload.source == 'admission_not_matched' else
                ('email_exports','email_not_matched.xlsx','Email'))
            result=state.get(stage,{}).get(filename)
            if not result:
                fail(f'Run {label} mapping first to use its Not matched students.')
            source={'name':filename,'data':result['data']}
        if not state.get('saved_admission_dump'):
            fail('Load the admission dump first.')
        school=read_snapshot(source,sheet)
        dump=read_saved_dump(state['saved_admission_dump'],values.get('admission_dump_sheet'))
        if 'generated_col' not in dump:
            fail('The admission dump has no generated_col column.')
        if school.empty:
            fail('No students in this file.')
        if payload.name_column not in school or payload.class_column not in school:
            fail('Choose the full name and Class Number columns.')
        signature=(payload.source,hashlib.sha256(source['data']).hexdigest(),
            hashlib.sha256(state['saved_admission_dump']['data']).hexdigest(),payload.name_column,payload.class_column,'account_unique_all_dump_rows_v5')
        result=map_by_full_name_class(school,dump,payload.name_column,payload.class_column)
        values.update(full_name_class_input_source=payload.source,
                      full_name_class_name_column=payload.name_column,full_name_class_class_column=payload.class_column)
        state['full_name_class_exports']=result
        state['full_name_class_result_signature']=signature
        return summary(state,session_id)
