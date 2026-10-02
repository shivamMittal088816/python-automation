"""Owner-only workspace naming endpoint."""
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, Response
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.workspaces.schemas import RenameWorkspaceRequest
from app.workspaces.services.identity import user_id
from app.workspaces.services.naming import rename_workspace

router = APIRouter()


@router.patch('/{workspace_id}')
def rename_owned_workspace(workspace_id: Annotated[str, Path(pattern=r'^[a-f0-9]{64}$')],
                           payload: RenameWorkspaceRequest, request: Request, response: Response,
                           db: Session = Depends(get_db)):
    result = rename_workspace(db, user_id(request), workspace_id, payload.name)
    response.headers['Cache-Control'] = 'no-store'
    return result
