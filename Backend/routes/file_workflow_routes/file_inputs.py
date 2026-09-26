"""Input files endpoints for the mapping API."""
from Backend.api.session_cookie import SessionId, WorkspaceRevision
from pathlib import Path
import logging
from fastapi import APIRouter, File, UploadFile
from Backend.config.settings import settings
from Backend.api.file_workflow_state import workspace
from Backend.schemas.file_workflow import FilePathInput, SchoolDetails, SchoolInput
from Backend.repositories.admission_dump_service import fetch_school_dump
from Backend.api.file_workflow_snapshots import add_snapshot
from Backend.api.file_workflow_validation import fail
from Backend.api.file_workflow_responses import summary
from Backend.api.file_workflow_invalidation import clear_all_mappings


router = APIRouter(tags=['Input files'])
logger = logging.getLogger('uvicorn.error')


@router.post('/files/{kind}')
def upload_file(session_id: SessionId, revision: WorkspaceRevision, kind: str, file: UploadFile = File(...)):
    try:
        data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
    except (OSError, ValueError):
        logger.exception('Failed to read an uploaded %s file.', kind)
        fail('Could not read the uploaded file. Choose the file again and retry.')
    if not data:
        fail('The uploaded file is empty.')
    if len(data) > settings.MAX_UPLOAD_BYTES:
        fail(f'The uploaded file exceeds the {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.', 413)
    with workspace(session_id, expected_revision=revision) as state:
        previous = state.get('saved_admission_school' if kind == 'school' else 'saved_admission_dump')
        changed = (not previous or previous.get('data') != data
                   or kind == 'dump' and bool(previous.get('school_index')))
        add_snapshot(state,kind,file.filename or '',data)
        if changed:
            clear_all_mappings(state)
        return summary(state,session_id)


@router.post('/files/{kind}/path')
def load_path(session_id: SessionId,revision: WorkspaceRevision,kind: str,payload: FilePathInput):
    if not settings.ALLOW_LOCAL_FILE_PATHS:
        fail('File path loading is disabled on this Backend.',403)
    value = payload.path.strip().strip('"')
    if not value or Path(value).suffix.lower() not in ('.csv','.xlsx'):
        fail('Could not load file: Enter a CSV or XLSX file path.')
    path=Path(value).expanduser()
    try:
        if path.stat().st_size > settings.MAX_UPLOAD_BYTES:
            fail(f'The selected file exceeds the {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.', 413)
        data=path.read_bytes()
    except OSError:
        logger.exception('Failed to read a local %s file path.', kind)
        fail('Could not load the selected file. Check that it exists and is readable.')
    if not data:
        fail('The selected file is empty.')
    with workspace(session_id, expected_revision=revision) as state:
        previous = state.get('saved_admission_school' if kind == 'school' else 'saved_admission_dump')
        changed = (not previous or previous.get('data') != data
                   or kind == 'dump' and bool(previous.get('school_index')))
        add_snapshot(state,kind,path.name,data,source=str(path),path=str(path))
        if changed:
            clear_all_mappings(state)
        return summary(state,session_id)


@router.post('/student-dump/fetch')
def fetch_dump(session_id: SessionId,revision: WorkspaceRevision,payload: SchoolInput):
    with workspace(session_id, expected_revision=revision) as state:
        index=payload.school_index.strip()
        if not index:
            fail('Enter a school index first.')
        try:
            dump=fetch_school_dump(index)
        except ValueError as exc:
            fail(str(exc))
        except Exception:
            logger.exception('Failed to fetch the admission dump from the database.')
            fail('Could not fetch dump data. Check the database connection and try again.',503)
        label=f"{dump.attrs['school_index']}-{dump.attrs['school_name']}"
        dump_data=dump.to_csv(index=False).encode('utf-8')
        previous=state.get('saved_admission_dump')
        changed=(not previous
                 or previous.get('data') != dump_data
                 or str(previous.get('school_index', '')).strip() != str(dump.attrs['school_index']).strip())
        # Publish the replacement only after the new school was validated and
        # fetched successfully. A failed fetch leaves the current workspace intact.
        state.pop('saved_admission_dump',None)
        if changed:
            clear_all_mappings(state)
        state.setdefault('admission_settings', {}).update(
            admission_dump_school_index=str(dump.attrs['school_index']),
            admission_dump_source='Fetch from SQL',
        )
        if not dump.empty:
            add_snapshot(state,'dump',f'school_{index}_dump.csv',dump_data,
                         source=f'SQL school {index}',school_index=dump.attrs['school_index'],school_name=dump.attrs['school_name'])
        return summary(state,session_id) | {'message':f'Fetched {len(dump)} student records for {label}.' if not dump.empty else f'No student records found for {label}.','message_type':'success' if not dump.empty else 'warning'}


@router.patch('/school')
def school_details(session_id: SessionId,revision: WorkspaceRevision,payload: SchoolDetails):
    index=payload.school_index.strip()
    name=payload.school_name.strip() if payload.school_name is not None else None
    if not index.isascii() or not index.isdecimal() or name == "":
        fail('Enter a numeric school index and, if provided, a nonempty school name.')
    with workspace(session_id, expected_revision=revision) as state:
        if not state.get('saved_admission_dump'):
            fail('Load the admission dump first.')
        snapshot=state['saved_admission_dump']
        changed = index != str(snapshot.get('school_index', '')).strip()
        state['saved_admission_dump']={key:snapshot[key] for key in snapshot} | {'school_index':index,'school_name':name if name is not None else snapshot.get('school_name','')}
        if changed:
            clear_all_mappings(state)
        return summary(state,session_id) | {'message':'School details saved with this dump.'}
