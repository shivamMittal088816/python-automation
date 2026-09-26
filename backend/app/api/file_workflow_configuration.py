"""Detect admission columns and maintain committed input configuration."""
import hashlib
from app.utils.table_queries import find_dump_column
from app.api.file_workflow_snapshots import read_snapshot, selected_sheet, sheets
from app.api.file_workflow_validation import fail


def suggest(columns, aliases, preferred=None, optional=False):
    if preferred in columns:
        return preferred
    normalize = lambda value: ''.join(char for char in str(value).lower() if char.isalnum())
    normalized = [normalize(column) for column in columns]
    for alias in aliases:
        if normalize(alias) in normalized:
            return columns[normalized.index(normalize(alias))]
    return None if optional or not columns else columns[0]


def admission_configuration(state, apply_settings=False):
    if not state.get('saved_admission_school') or not state.get('saved_admission_dump'):
        state.pop('admission_exports', None)
        return None
    values = state.setdefault('admission_settings', {})
    school_sheet, dump_sheet = selected_sheet(state,'school'), selected_sheet(state,'dump')
    school = read_snapshot(state['saved_admission_school'],school_sheet)
    dump = read_snapshot(state['saved_admission_dump'],dump_sheet)
    if not len(school.columns) or not len(dump.columns):
        fail('Both files must contain column headers.')
    aliases = ['admission_number','admission_no','admission','admission_id','adm_no','adm_number','admno']
    if not values.get('admission_header_detection_v2'):
        detected = suggest(list(school.columns), aliases)
        first = school.columns[0]
        normalize = lambda value: ''.join(char for char in str(value).lower() if char.isalnum())
        if detected != first and values.get('school_admission_col') == first and normalize(first) not in [normalize(alias) for alias in aliases]:
            values['school_admission_col'] = detected
        values['admission_header_detection_v2'] = True
    school_admission = suggest(list(school.columns), aliases, values.get('school_admission_col'))
    name_column = suggest(list(school.columns), ['first_name','firstname','first'], values.get('school_name_col'))
    values.update(school_admission_col=school_admission, school_name_col=name_column,
                  admission_school_sheet=school_sheet, admission_dump_sheet=dump_sheet)
    dump_admission = find_dump_column(dump, aliases)
    username = find_dump_column(dump, ['user_name','username','user_username'])
    dump_first_name = find_dump_column(dump, ['user_firstname','first_name','firstname','first'])
    missing = [label for label,column in [('admission_number',dump_admission),('user_name or Username',username),('user_firstname',dump_first_name)] if column is None]
    signature = (hashlib.sha256(state['saved_admission_school']['data'] + state['saved_admission_dump']['data']).hexdigest(),
                 school_sheet,dump_sheet,school_admission,dump_admission,username,name_column,dump_first_name,'status_with_reason_v11')
    previous = tuple(state.get('admission_signature') or ())
    # File replacement still invalidates results; dropdown edits alone do not.
    files_changed = bool(previous and previous[0] != signature[0])
    if apply_settings or files_changed or not previous:
        if previous != signature:
            state.pop('admission_exports', None)
        state['admission_signature'] = signature
    if missing and (apply_settings or files_changed):
        state.pop('admission_exports',None)
    hits = int(school[school_admission].astype(str).str.strip().isin(set(dump[dump_admission].astype(str).str.strip())- {''}).sum()) if dump_admission else 0
    return {'school_columns':list(school.columns),'dump_columns':list(dump.columns),
        'school_sheets':sheets(state['saved_admission_school']),'dump_sheets':sheets(state['saved_admission_dump']),
        'dump_admission':dump_admission,'username':username,'dump_first_name':dump_first_name,
        'missing_columns':missing,'admission_hits':hits,'school_rows':len(school),
        'duplicate_rows':int(school.duplicated(keep=False).sum()),'dropped_rows':int(school.duplicated(keep='first').sum())}
