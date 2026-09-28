"""Create a workflow session, set its browser cookie and return its UI summary."""
from fastapi import APIRouter, Response

from app.api.session_cookie import set_session_cookie
from app.api.file_workflow_state import create_session, workspace
from app.schemas.file_workflow import CreateSession
from app.api.file_workflow_responses import summary


router = APIRouter(tags=['Mapping sessions'])


@router.post('/session')
def new_session(payload: CreateSession, response: Response):
    session_id = create_session(payload.school_index)
    set_session_cookie(response, session_id)
    with workspace(session_id, persist=False) as state:
        return summary(state, session_id)

# Purpose: Create a workflow session, set its browser cookie and return its UI summary.
# Its public interface includes new_session.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.file_workflows.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
