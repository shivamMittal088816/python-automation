"""Workspace-scoped lookup for browser upload attempts."""

from fastapi import APIRouter

from app.api.session_cookie import SessionId
from app.schemas.operation import OperationStatusInput
from app.services.operation_log import operations_by_client_id


router = APIRouter(tags=['Operation recovery'])


@router.post('/operations/status')
def operation_status(session_id: SessionId, payload: OperationStatusInput):
    ids = [str(value) for value in payload.client_operation_ids]
    return {'operations': operations_by_client_id('mapping', session_id, ids)}
