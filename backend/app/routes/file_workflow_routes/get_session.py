"""Restore the current workflow session and return its UI summary."""
from fastapi import APIRouter

from app.api.session_cookie import SessionId
from app.api.file_workflow_state import workspace
from app.api.file_workflow_responses import summary


router = APIRouter(tags=['Mapping sessions'])


@router.get('/session')
def get_session(session_id: SessionId):
    with workspace(session_id, persist=False) as state:
        return summary(state, session_id)

# Purpose: Restore the current workflow session and return its UI summary.
# Its public interface includes get_session.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.file_workflows.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
