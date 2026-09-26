"""Email mapping endpoints for the mapping API."""
from app.api.session_cookie import SessionId, WorkspaceRevision
import logging
from fastapi import APIRouter
from sqlalchemy.exc import SQLAlchemyError
from app.api.file_workflow_state import workspace
from app.schemas.file_workflow import EmailInput
from app.repositories.email_dump_service import fetch_email_dump
from app.services.email_mapping.email_file_mapping import sync_email_stage
from app.services.email_mapping.email_file_mapping import map_by_email
from app.api.file_workflow_validation import fail
from app.api.file_workflow_snapshots import read_snapshot
from app.api.file_workflow_responses import summary
from app.api.file_workflow_invalidation import clear_class_mapping


router = APIRouter(tags=['Email mapping'])
logger = logging.getLogger('uvicorn.error')


@router.post('/email-mapping/run')
def email_map(session_id: SessionId,revision: WorkspaceRevision,payload: EmailInput):
    with workspace(session_id, expected_revision=revision) as state:
        if not sync_email_stage(state):
            fail('Load a school file first.')
        values=state.setdefault('admission_settings',{})
        if payload.source == 'admission_not_matched':
            admission_result=state.get('admission_exports',{}).get('not_matched.xlsx')
            if not admission_result:
                fail('Run Admission mapping first to use its Not matched students for Email mapping.')
            school=read_snapshot({'name':'not_matched.xlsx','data':admission_result['data']})
        else:
            school=read_snapshot(state['saved_admission_school'], values.get('admission_school_sheet'))
        if payload.email_column not in school or payload.name_column not in school:
            fail('Choose the school email and first name columns.')
        school_index=(state.get('saved_admission_dump',{}).get('school_index')
                      or values.get('workspace_school_index'))
        try:
            dump=fetch_email_dump(school[payload.email_column])
            result=map_by_email(school,dump,payload.email_column,'user_email',payload.name_column,school_index=school_index)
        except (SQLAlchemyError, ConnectionError, TimeoutError):
            logger.exception('Failed to fetch the email dump from the database.')
            fail('Could not fetch or map the email dump. Check the database connection and try again.',503)
        except (ValueError, KeyError, OSError) as exc:
            logger.warning('Email mapping rejected invalid input: %s', exc)
            fail('Could not map these files. Check the selected email and name columns.')
        values.update(email_input_source=payload.source,email_input_column=payload.email_column,
                      email_first_name_column=payload.name_column)
        state['saved_email_dump']={'name':'email_dump.csv','data':dump.to_csv(index=False).encode('utf-8')}
        state['email_exports']=result
        state['email_result_signature']=(state['email_source_signature'],payload.source,payload.email_column,
                                         payload.name_column,'email_first_name_school_v13',school_index)
        clear_class_mapping(state)
        return summary(state,session_id)
