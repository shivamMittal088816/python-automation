"""School file, admission dump, email dump and source-table previews."""
from app.api.session_cookie import SessionId
from fastapi import APIRouter, Query
from app.api.file_workflow_state import workspace
from app.utils.school_statistics import dump_overview, inferred_school_index, school_class_statistics
from app.api.file_workflow_constants import FILES
from app.api.file_workflow_validation import fail
from app.api.file_workflow_responses import page_response, records
from app.api.file_workflow_snapshots import read_snapshot, selected_sheet
from app.api.file_workflow_configuration import suggest


router = APIRouter(tags=['Mapping previews'])


@router.get('/table-previews/{kind}')
def table_view(session_id: SessionId,kind: str,sheet: str | None=None,query: str='',
               columns: list[str] | None=Query(None),page: int=Query(1,ge=1),limit: int=Query(50,ge=0),
               class_column: str | None=None,section_column: str | None=None):
    with workspace(session_id,persist=False) as state:
        if kind not in FILES or not state.get(FILES[kind]):
            fail('No file available.',404)
        snapshot=state[FILES[kind]]
        rows=read_snapshot(snapshot,selected_sheet(state,kind,sheet))
        if columns and any(column not in rows for column in columns):
            fail('Choose valid search columns.')
        result=page_response(rows,page,limit,query,columns)
        values=state.get('admission_settings',{})
        cols=list(rows.columns)
        email_preferred=values.get('email_input_column')
        if email_preferred not in cols or email_preferred is None:
            email_preferred=next((column for column in cols if 'email' in ''.join(char for char in str(column).lower() if char.isalnum())),None)
        name_preferred=values.get('email_full_name_column')
        if name_preferred not in cols:
            name_preferred=next((column for column in cols if str(column).lower().replace('_','').replace(' ','') in ('fullname','studentfullname','studentname')),values.get('school_name_col'))
        if name_preferred not in cols:
            name_preferred=cols[0] if cols else None
        result['suggestions']={
            'email_column':email_preferred,
            'first_name_column':suggest(cols,['firstname','first','studentfirstname'],values.get('school_name_col')),
            'full_name_column':name_preferred,
            'class_number_column':suggest(cols,['classnumber','classno','classnum'],values.get('full_name_class_class_column')),
            'class_column':suggest(cols,['class','classname','classnumber','classno','grade'],values.get('school_overview_class_column'),optional=True),
            'section_column':suggest(cols,['section','sectionname','sectionno','useredumajor'],values.get('school_overview_section_column'),optional=True),
        }
        if kind=='dump':
            overview,count=dump_overview(rows)
            result.update(overview=records(overview) if overview is not None else None,student_count=count,inferred_school_index=inferred_school_index(rows),has_generated_col='generated_col' in rows)
        elif kind=='school' and class_column and section_column:
            if class_column not in rows or section_column not in rows:
                fail('Choose valid class and section columns.')
            try:
                result['overview']=records(school_class_statistics(rows,class_column,section_column))
            except ValueError as exc:
                fail(str(exc))
        return result
