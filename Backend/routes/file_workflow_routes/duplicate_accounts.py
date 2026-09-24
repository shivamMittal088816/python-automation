"""Duplicate accounts endpoints for the mapping API."""
from Backend.api.session_cookie import SessionId
from fastapi import APIRouter
from Backend.api.file_workflow_state import workspace
from Backend.services.shared_mapping.mapping_account_uniqueness import review_duplicate_accounts
from Backend.api.file_workflow_responses import summary


router = APIRouter(tags=['Duplicate accounts'])


@router.post('/duplicate-accounts/reconcile')
def reconcile_accounts(session_id: SessionId):
    with workspace(session_id) as state:
        review_duplicate_accounts(state)
        return summary(state,session_id)
