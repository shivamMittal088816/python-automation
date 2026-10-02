"""Workspace dropdown listing endpoint."""
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from app.config.dependencies import get_db
from app.workspaces.schemas import Workflow
from app.workspaces.services.identity import user_id
from app.workspaces.services.listing import list_account_workspaces

router = APIRouter()


@router.get('')
def list_workspaces(request: Request, response: Response, workflow: Workflow, db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    return list_account_workspaces(db, user_id(request), workflow)
