"""Execute the verified, sanity-checked rollback transaction."""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.rollback_update_repository import (
    apply_rollback_updates, preview_rollback_updates,
)
from app.routes.rollback.access import workspace_for
from app.services import rollback as rollback_storage
from app.services.tabular_file import read_frame


router = APIRouter()


class RollbackCommitInput(BaseModel):
    preview_token: str = Field(min_length=64, max_length=64, pattern=r'^[a-f0-9]{64}$')


def _validated_input(request, response):
    workspace_id = workspace_for(request, response)
    if not workspace_id:
        raise HTTPException(409, 'Verify a school and upload a rollback file first.')
    state = rollback_storage.load_state(workspace_id)
    school = state.get('school')
    if not isinstance(school, dict) or not school.get('school_index'):
        raise HTTPException(409, 'Verify a school before performing rollback.')
    if not isinstance(state.get('input'), dict):
        raise HTTPException(409, 'Upload a rollback file before performing rollback.')
    metadata, data = rollback_storage.read_input(workspace_id)
    frame = read_frame(metadata.get('name', ''), data, metadata.get('sheet'))
    sanity = rollback_storage.check_rollback_input(frame)
    if not sanity['valid']:
        raise HTTPException(422, sanity['message'])
    return frame, str(school['school_index'])


@router.post('/preview-changes')
def preview_rollback_changes(request: Request, response: Response):
    frame, school_index = _validated_input(request, response)
    try:
        return preview_rollback_updates(frame, school_index)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'Could not analyze rollback changes.') from exc


@router.post('/run')
def run_rollback(payload: RollbackCommitInput, request: Request, response: Response):
    frame, school_index = _validated_input(request, response)
    try:
        result = apply_rollback_updates(frame, school_index, payload.preview_token)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'The rollback transaction could not be completed.') from exc
    return {
        **result,
        'message': (
            f"Rollback completed: {result['supplied_excluded']} uploaded user IDs were excluded "
            f"and {result['fallback_updated']} non-supplied package-14 users changed."
        ),
    }
