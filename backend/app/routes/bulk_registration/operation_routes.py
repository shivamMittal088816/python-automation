"""Workspace-scoped lookup for browser upload attempts."""

from fastapi import APIRouter, Request, Response

from app.routes.bulk_registration.workspace_access import workspace_for
from app.schemas.operation import OperationStatusInput
from app.services.operation_log import operations_by_client_id


router = APIRouter()


@router.post('/operations/status')
def operation_status(payload: OperationStatusInput, request: Request, response: Response):
    workspace_id, _ = workspace_for(request, response)
    ids = [str(value) for value in payload.client_operation_ids]
    return {'operations': operations_by_client_id('bulk', workspace_id, ids)}
