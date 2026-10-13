"""Rollback database-dump preview and download routes."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse
from openpyxl.utils.exceptions import IllegalCharacterError
from starlette.background import BackgroundTask

from app.routes.rollback.access import workspace_for
from app.routes.rollback.constants import DUMP_PREVIEW_PAGE_SIZE
from app.routes.rollback.dump_export import export_dump_file
from app.services import rollback as rollback_storage


router = APIRouter(prefix='/dump')


@router.get('/preview')
def preview_rollback_dump(request: Request, response: Response, page: int = 1):
    workspace_id = workspace_for(request, response)
    if not workspace_id:
        raise HTTPException(409, 'Verify a school first.')
    return rollback_storage.read_dump_page(
        workspace_id, page, DUMP_PREVIEW_PAGE_SIZE,
    )


@router.get('/download')
def download_rollback_dump(
    request: Request,
    response: Response,
    file_format: Literal['csv', 'xlsx'] = 'csv',
):
    workspace_id = workspace_for(request, response)
    if not workspace_id:
        raise HTTPException(409, 'Verify a school first.')
    state = rollback_storage.load_state(workspace_id)
    school = state.get('school')
    if not isinstance(school, dict) or not school.get('school_index'):
        raise HTTPException(409, 'Verify a school first.')
    try:
        exported = export_dump_file(workspace_id, file_format)
    except (ValueError, IllegalCharacterError) as exc:
        raise HTTPException(
            400,
            'Could not create the dump file. Download CSV or check for invalid '
            'spreadsheet characters.',
        ) from exc
    filename = f'rollback-dump-{school["school_index"]}.{file_format}'
    media_type = (
        'text/csv; charset=utf-8'
        if file_format == 'csv'
        else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    return FileResponse(
        exported,
        media_type=media_type,
        filename=filename,
        headers={'Cache-Control': 'no-store'},
        background=BackgroundTask(exported.unlink, missing_ok=True),
    )
