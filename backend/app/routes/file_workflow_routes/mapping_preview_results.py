"""Paginated Matched, Review and Not Matched previews for all mapping stages."""
import hashlib

from fastapi import APIRouter, Query

from app.api.session_cookie import SessionId
from app.api.file_workflow_state import workspace
from app.api.file_workflow_constants import FILES, STAGES
from app.api.file_workflow_validation import fail
from app.api.file_workflow_responses import page_response
from app.api.file_workflow_snapshots import read_snapshot, selected_sheet
from app.utils.table_queries import find_dump_column
from app.utils.workbook_operations import move_students, remove_original_columns


router = APIRouter(tags=['Mapping previews'])


@router.get('/result-previews/{stage}/{filename}')
def result_view(session_id: SessionId,stage: str,filename: str,page: int=Query(1,ge=1),limit: int=Query(50,ge=1)):
    with workspace(session_id,persist=False) as state:
        if stage not in STAGES:
            fail('Result stage not found.',404)
        exports = state.get(STAGES[stage], {})
        if stage=='admission' and exports:
            exports=remove_original_columns(exports)
            if 'new_students.xlsx' in exports:
                if exports['new_students.xlsx']['count']:
                    exports=move_students(exports,'new_students.xlsx',list(range(exports['new_students.xlsx']['count'])),'not_matched.xlsx')
                exports.pop('new_students.xlsx')
        snapshot=exports.get(filename)
        if not snapshot:
            fail('Result group not found.',404)
        rows=read_snapshot({'name':filename,'data':snapshot['data']})
        dump = None
        dump_fullname = None
        if stage == 'admission' and state.get(FILES['dump']):
            dump = read_snapshot(state[FILES['dump']], selected_sheet(state, 'dump'))
            dump_fullname = find_dump_column(dump, ['fullname', 'full_name'])
            dump_admission = find_dump_column(dump, ['admission_number', 'admission_no', 'admission', 'admission_id', 'adm_no', 'adm_number', 'admno'])
            if dump_fullname is not None and dump_admission is not None:
                # Enrich existing saved previews too, without rerunning mapping.
                # Keep all candidate names when an admission occurs more than once.
                names = {}
                for admission, name in zip(dump[dump_admission].fillna(''), dump[dump_fullname].fillna('')):
                    admission = str(admission).strip()
                    if admission and str(name):
                        names.setdefault(admission, []).append(str(name))
                if 'mapping_admission_number' in rows:
                    rows['mapping_dump_full_name'] = rows['mapping_admission_number'].fillna('').map(
                        lambda value: '\n'.join(dict.fromkeys(names.get(str(value).strip(), []))))
        result=page_response(rows,page,limit)
        result['version']=hashlib.sha256(snapshot['data']).hexdigest()
        values=state.get('admission_settings',{})
        first=([values.get('school_admission_col'),values.get('school_name_col'),'mapping_dump_first_name','mapping_dump_full_name','mapping_username','mapping_user_id','mapping_status'] if stage=='admission' else
               [values.get('email_input_column'),values.get('email_first_name_column'),values.get('email_full_name_column'),'email_mapping_dump_full_name','email_mapping_status','email_mapping_username','email_mapping_user_id'] if stage=='email' else
               [values.get('full_name_class_name_column'),values.get('full_name_class_class_column'),'full_name_class_generated_value','full_name_class_status','full_name_class_username','full_name_class_user_id'])
        result['columns']=list(dict.fromkeys([column for column in first if column in rows]+list(rows.columns)))
        result['column_labels']={'mapping_first_name':'School first name','mapping_dump_first_name':'Dump first name used','mapping_username':'Dump username used',
            'mapping_status':'Status and reason','email_mapping_status':'Status and reason','email_mapping_dump_full_name':'Dump first name used'}
        if stage == 'admission':
            dump_name = (find_dump_column(dump, ['user_firstname', 'first_name', 'firstname', 'first'])
                         if dump is not None else None) or 'user_firstname'
            dump_username = (find_dump_column(dump, ['user_name', 'username', 'user_username'])
                             if dump is not None else None) or 'user_name'
            # Label only generated evidence; original school headers stay untouched.
            result['column_labels'] = {
                'mapping_dump_first_name': f'dump_{dump_name}',
                'mapping_dump_full_name': f'dump_{dump_fullname or "fullname"}',
                'mapping_username': f'dump_{dump_username}',
                'mapping_user_id': 'dump_user_id',
                'mapping_dump_row': 'dump_row',
                'mapping_dump_count': 'dump_match_count',
                'mapping_admission_number': 'Mapping admission number (trimmed)',
                'mapping_first_name': 'School first name (comparison value)',
                'mapping_status': 'Status and reason',
            }
        return result
