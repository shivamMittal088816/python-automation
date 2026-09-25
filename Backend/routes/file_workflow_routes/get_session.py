"""Restore the current workflow session and return its UI summary."""
from fastapi import APIRouter

from Backend.api.session_cookie import SessionId
from Backend.api.file_workflow_state import workspace
from Backend.api.file_workflow_responses import summary


router = APIRouter(tags=['Mapping sessions'])


@router.get('/session')
def get_session(session_id: SessionId):
    with workspace(session_id, persist=False) as state:
        return summary(state, session_id)
