"""Create a workflow session, set its browser cookie and return its UI summary."""
from fastapi import APIRouter, Response

from Backend.api.session_cookie import set_session_cookie
from Backend.api.file_workflow_state import create_session, workspace
from Backend.schemas.file_workflow import CreateSession
from Backend.api.file_workflow_responses import summary


router = APIRouter(tags=['Mapping sessions'])


@router.post('/session')
def new_session(payload: CreateSession, response: Response):
    session_id = create_session(payload.school_index)
    set_session_cookie(response, session_id)
    with workspace(session_id, persist=False) as state:
        return summary(state, session_id)
