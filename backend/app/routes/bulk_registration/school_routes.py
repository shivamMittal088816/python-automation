"""School verification and authoritative school-state endpoints."""
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError

from app.routes.bulk_registration.models import SchoolInput
from app.routes.bulk_registration.workspace_access import require_revision, workspace_for, workspace_summary
from app.services.bulk_registration import SchoolNotFoundError, fetch_school
from app.services.bulk_registration_storage import save_workspace, workspace_locked


router = APIRouter()
Revision = Annotated[int, Header(alias='X-Workspace-Revision', ge=0)]


def get_school(school_index: str):
    try:
        return fetch_school(school_index)
    except SchoolNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'School verification failed. Check the database connection and try again.') from exc


@router.get('/schools/{school_index}')
def verify_school(school_index: str):
    return get_school(school_index)


@router.post('/school')
@workspace_locked
def set_school(payload: SchoolInput, request: Request, response: Response, expected_revision: Revision):
    school = get_school(payload.school_index)
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    state.update({'school_index': school['school_index'], 'school': school,
                  'output': None, 'outputs': {}, 'output_verified': False,
                  'revision': expected_revision + 1})
    save_workspace(workspace_id, state)
    return workspace_summary(state)

# Purpose: School verification and authoritative school-state endpoints.
# Its public interface includes get_school, verify_school, set_school.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.__init__, app.routes.bulk_registration.compatibility, app.routes.bulk_registration.conversion_routes.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
