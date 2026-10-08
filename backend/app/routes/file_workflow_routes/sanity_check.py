"""Run schema-aware sanity rules on the selected mapping school worksheet."""
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.api.session_cookie import SessionId, WorkspaceRevision
from app.api.file_workflow_state import workspace
from app.api.file_workflow_snapshots import read_snapshot, selected_sheet
from app.schemas.file_workflow import AdmissionRunInput
from app.repositories.house_repository import fetch_houses
from app.services.mapping_input_sanity import check_school_input
from app.services.bulk_registration_sanity.house import house_columns


router = APIRouter(tags=['Admission mapping'])


@router.post('/sanity-check')
def sanity_check(session_id: SessionId, revision: WorkspaceRevision,
                 payload: AdmissionRunInput):
    with workspace(session_id, persist=False, expected_revision=revision) as state:
        snapshot = state.get('saved_admission_school')
        if not snapshot:
            raise HTTPException(409, 'Load a school file first.')
        sheet = selected_sheet(state, 'school', payload.admission_school_sheet)
        frame = read_snapshot(snapshot, sheet)
        try:
            houses = fetch_houses() if house_columns(frame) else ()
        except SQLAlchemyError as exc:
            raise HTTPException(503, 'Could not check houses against the dump. Try again.') from exc
        settings = state.get('admission_settings', {})
        return check_school_input(
            frame, houses=houses,
            name_column=payload.school_name_col or settings.get('school_name_col'),
            admission_column=payload.school_admission_col or settings.get('school_admission_col'),
        )
