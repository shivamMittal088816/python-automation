"""Owner-only soft deletion of account workspaces."""
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, Response
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.workspaces.services.deletion import soft_delete_workspace
from app.workspaces.services.identity import user_id

router = APIRouter()


@router.delete('/{workspace_id}')
def delete_owned_workspace(workspace_id: Annotated[str, Path(pattern=r'^[a-f0-9]{64}$')],
                           request: Request, response: Response,
                           db: Session = Depends(get_db)):
    result = soft_delete_workspace(db, user_id(request), workspace_id)
    response.headers['Cache-Control'] = 'no-store'
    return result
