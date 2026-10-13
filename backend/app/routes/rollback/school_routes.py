"""Rollback school verification and clearing routes."""

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.rollback_dump_repository import stream_rollback_dump
from app.routes.rollback.access import workspace_for
from app.routes.rollback.constants import DUMP_PREVIEW_PAGE_SIZE
from app.schemas.file_workflow import SchoolInput
from app.services import rollback as rollback_storage
from app.services.bulk_registration import fetch_school
from app.services.school_lookup import resolve_school


router = APIRouter()


@router.post('/school')
def set_rollback_school(payload: SchoolInput, request: Request, response: Response):
    school = resolve_school(fetch_school, payload.school_index)
    try:
        with stream_rollback_dump(school['school_index']) as (columns, rows):
            workspace_id = workspace_for(request, response, create=True)
            rollback_storage.save_school_rows(workspace_id, school, columns, rows)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            503, 'Could not fetch the rollback dump from the database.',
        ) from exc
    return {
        'school': school,
        'dump': rollback_storage.read_dump_page(
            workspace_id, 1, DUMP_PREVIEW_PAGE_SIZE,
        ),
    }


@router.delete('/school')
def clear_rollback_school(request: Request, response: Response):
    workspace_id = workspace_for(request, response)
    if workspace_id:
        rollback_storage.clear_school(workspace_id)
    return {'school': None, 'dump': None}
