"""Build workspace summaries, committed run details and paged table responses."""
import hashlib
from fastapi import HTTPException
from app.api.file_workflow_constants import FILES, STAGES
from app.api.file_workflow_configuration import admission_configuration
from app.api.file_workflow_snapshots import read_snapshot, sheets
from app.utils.table_queries import preview_page_bounds, search_dump
from app.services.email_mapping.email_input import email_input_signature


def records(rows):
    return rows.fillna('').to_dict(orient='records')


def mapping_run_columns(state):
    """Describe saved results using committed signatures, never draft selections."""
    columns = {'admission': {}, 'email': {}, 'full_name_class': {}}
    admission = state.get('admission_signature') or ()
    if state.get('admission_exports') and len(admission) > 6:
        columns['admission']['1'] = [admission[3], admission[6]]
    email = state.get('email_result_signature') or ()
    if state.get('email_exports') and len(email) > 2:
        columns['email']['1'] = list(email[2:4] if len(email) == 6 else email[1:3])
    full_name = state.get('full_name_class_result_signature') or ()
    if state.get('full_name_class_exports') and len(full_name) >= 6:
        columns['full_name_class']['1'] = [full_name[3], full_name[4]]
    return columns


def summary(state, session_id):
    error = None
    try:
        config = admission_configuration(state)
    except HTTPException as exc:
        config = None
        error = exc.detail
    except (ValueError, KeyError, OSError):
        config = None
        error = 'Could not inspect the mapping configuration. Check the selected files and sheets.'
    ready = bool(email_input_signature(state))
    return {'workspace_id':state['workspace_id'],'revision':int(state.get('revision',0)),'files':{kind:{key:state[field][key] for key in state[field] if key!='data'} | {'sheets':sheets(state[field]), 'version':hashlib.sha256(state[field]['data']).hexdigest()} for kind,field in FILES.items() if state.get(field)},
        'settings':state.get('admission_settings',{}),'configuration':config,'configuration_error':error,
        'exports':{stage:{name:item['count'] for name,item in state.get(field,{}).items()} for stage,field in STAGES.items()},
        'export_versions':{stage:{name:hashlib.sha256(item['data']).hexdigest() for name,item in state.get(field,{}).items()} for stage,field in STAGES.items()},
        'email_ready':ready,
        'run_columns':mapping_run_columns(state)}


def page_response(rows,page,limit,query='',columns=None):
    results=search_dump(rows,query if columns!=[] else '',columns)
    if limit:
        page,pages,offset,end=preview_page_bounds(len(results),limit,page)
    else:
        page,pages,offset,end=1,1,0,len(results)
    return {'columns':list(rows.columns),'rows':records(results.iloc[offset:end]),'total':len(rows),
        'found':len(results),'page':page,'pages':pages,'offset':offset,'end':end}
