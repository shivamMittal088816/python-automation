"""Build workspace summaries, committed run details and paged table responses."""
import hashlib
from uuid import uuid4
from fastapi import HTTPException
from Backend.api.file_workflow_constants import FILES, STAGES
from Backend.api.file_workflow_configuration import admission_configuration
from Backend.api.file_workflow_snapshots import read_snapshot, sheets
from Backend.utils.table_queries import preview_page_bounds, search_dump
from Backend.services.email_mapping.email_file_mapping import sync_email_stage
from Backend.services.email_mapping.email_input import email_pass_one_complete


def records(rows):
    return rows.fillna('').to_dict(orient='records')


def result_pass(state, stage):
    exports = state.get(STAGES[stage], {})
    if not exports:
        return 0
    values = state.setdefault('admission_settings', {})
    key = f'{stage}_result_pass'
    if key not in values:
        # Recover the displayed pass for results saved before pass tracking existed.
        prefix = 'email_' if stage == 'email' else ''
        status = 'email_mapping_status' if stage == 'email' else 'mapping_status'
        values[key] = 1
        for group in ('matched', 'review'):
            filename = f'{prefix}{group}.xlsx'
            snapshot = exports.get(filename)
            if snapshot and snapshot['count']:
                rows = read_snapshot({'name': filename, 'data': snapshot['data']})
                if status in rows and rows[status].astype(str).str.contains('Pass 2:', regex=False).any():
                    values[key] = 2
                    break
    return values[key]


def mapping_run_columns(state):
    """Describe saved results using committed signatures, never draft selections."""
    columns = {'admission': {}, 'email': {}, 'full_name_class': {}}
    admission = state.get('admission_signature') or ()
    if state.get('admission_exports') and len(admission) > 6:
        columns['admission']['1'] = [admission[3], admission[6]]
        if result_pass(state, 'admission') == 2:
            name = state.get('admission_settings', {}).get('admission_round_two_name_column')
            if name:
                columns['admission']['2'] = [admission[3], name]
    email = state.get('email_result_signature') or ()
    if state.get('email_exports') and len(email) > 2:
        columns['email']['1'] = [email[1], email[2]]
        if result_pass(state, 'email') == 2:
            name = state.get('admission_settings', {}).get('email_full_name_column')
            if name:
                columns['email']['2'] = [name]
    full_name = state.get('full_name_class_result_signature') or ()
    if state.get('full_name_class_exports') and len(full_name) >= 6:
        columns['full_name_class']['1'] = [full_name[3], full_name[4]]
        if len(full_name) >= 9:
            columns['full_name_class']['2'] = [full_name[7], full_name[8]]
    return columns


def summary(state, session_id):
    error = None
    try:
        config = admission_configuration(state)
    except (ValueError, KeyError, OSError, HTTPException) as exc:
        config = None
        error = exc.detail if isinstance(exc,HTTPException) else f'Could not map these files: {exc}'
    ready = sync_email_stage(state)
    return {'workspace_id':state.setdefault('workspace_id', str(uuid4())),'files':{kind:{key:state[field][key] for key in state[field] if key!='data'} | {'sheets':sheets(state[field]), 'version':hashlib.sha256(state[field]['data']).hexdigest()} for kind,field in FILES.items() if state.get(field)},
        'settings':state.get('admission_settings',{}),'configuration':config,'configuration_error':error,
        'exports':{stage:{name:item['count'] for name,item in state.get(field,{}).items()} for stage,field in STAGES.items()},
        'export_versions':{stage:{name:hashlib.sha256(item['data']).hexdigest() for name,item in state.get(field,{}).items()} for stage,field in STAGES.items()},
        'email_ready':ready,
        'run_columns':mapping_run_columns(state),
        'admission_result_pass':result_pass(state, 'admission'),
        'email_result_pass':result_pass(state, 'email'),
        'email_pass_one_complete':email_pass_one_complete(state),
        'full_name_class_round':(2 if len(state.get('full_name_class_result_signature') or ()) > 6 else 1) if state.get('full_name_class_exports') else 0,
        'full_name_class_round_one_not_matched':(state.get('full_name_class_round_one_exports') or state.get('full_name_class_exports',{})).get('full_name_class_not_matched.xlsx',{}).get('count',0)}


def page_response(rows,page,limit,query='',columns=None):
    results=search_dump(rows,query if columns!=[] else '',columns)
    if limit:
        page,pages,offset,end=preview_page_bounds(len(results),limit,page)
    else:
        page,pages,offset,end=1,1,0,len(results)
    return {'columns':list(rows.columns),'rows':records(results.iloc[offset:end]),'total':len(rows),
        'found':len(results),'page':page,'pages':pages,'offset':offset,'end':end}
