"""Paginated output preview and CSV/XLSX download endpoint."""
from io import BytesIO
from math import ceil
from typing import Annotated, Literal

import pandas as pd
from fastapi import APIRouter, File, Form, Header, HTTPException, Request, Response, UploadFile
from openpyxl.utils.exceptions import IllegalCharacterError
from sqlalchemy.exc import SQLAlchemyError

from app.mappings.bulk_registration.section import apply_section_ids
from app.repositories.section_repository import fetch_sections
from app.routes.bulk_registration.file_reading import read_frame
from app.routes.bulk_registration.school_routes import get_school
from app.routes.bulk_registration.workspace_access import require_revision, workspace_for, workspace_summary
from app.services.bulk_registration import convert_frame, export_frame
from app.services.bulk_registration_storage import read_snapshot, save_workspace, workspace_locked


router = APIRouter()
OUTPUT_PREVIEW_PAGE_SIZE = 20
Revision = Annotated[int, Header(alias='X-Workspace-Revision', ge=0)]


def paginated_summary(name, output, school, sheet, page, missing_sections):
    if page < 1:
        raise HTTPException(400, 'Preview page must be 1 or greater.')
    total_pages = max(1, ceil(len(output) / OUTPUT_PREVIEW_PAGE_SIZE))
    if page > total_pages:
        raise HTTPException(400, 'The requested preview page does not exist.')
    start = (page - 1) * OUTPUT_PREVIEW_PAGE_SIZE
    preview = output.iloc[start:start + OUTPUT_PREVIEW_PAGE_SIZE]
    return {'name': name, 'row_count': len(output), 'columns': list(output.columns),
            'rows': preview.values.tolist(), 'school': school, 'page': page,
            'page_size': OUTPUT_PREVIEW_PAGE_SIZE, 'total_pages': total_pages, 'sheet': sheet,
            'missing_sections': missing_sections}


def read_authoritative_output(workspace_id, state):
    reference = state.get('outputs', {}).get('authoritative')
    metadata, data = read_snapshot(workspace_id, reference)
    try:
        output = pd.read_csv(BytesIO(data), dtype=str, keep_default_na=False)
    except Exception as exc:
        raise HTTPException(409, 'Saved bulk registration output is unreadable. Generate the preview again.') from exc
    return metadata, output


@router.get('/output')
@workspace_locked
def get_output_page(request: Request, response: Response, page: int = 1):
    workspace_id, state = workspace_for(request, response)
    if not state.get('output'):
        raise HTTPException(409, 'Generate the output preview first.')
    metadata, output = read_authoritative_output(workspace_id, state)
    summary = paginated_summary(
        metadata.get('source_name', ''), output, metadata.get('school'),
        metadata.get('sheet'), page, metadata.get('missing_sections', []),
    )
    visible_state = dict(state)
    visible_state['output'] = summary
    return workspace_summary(visible_state)


@router.post('/convert')
@workspace_locked
def convert_workspace_file(
    request: Request, response: Response, expected_revision: Revision,
    school_index: str = Form(...), file_format: Literal['preview', 'csv', 'xlsx'] = Form('preview'),
    file: UploadFile | None = File(None), path: str | None = Form(None),
    sheet: Annotated[str | None, Form()] = None, page: Annotated[int, Form()] = 1,
):
    if file is not None or path is not None:
        raise HTTPException(400, 'Use the file already saved in the bulk workspace.')
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    metadata, data = read_snapshot(workspace_id, state.get('input'))
    name = metadata.get('name', '')
    sheet = metadata.get('sheet') if sheet is None else sheet
    school = get_school(school_index)
    if file_format == 'preview':
        try:
            output = convert_frame(read_frame(name, data, sheet), school)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        try:
            missing_sections = apply_section_ids(output, fetch_sections())
        except SQLAlchemyError as exc:
            raise HTTPException(503, 'Could not verify sections. Check the database connection and try again.') from exc
        summary = paginated_summary(name, output, school, sheet, page, missing_sections)
        state.update({'school_index': school['school_index'], 'school': school,
                      'output': summary, 'outputs': {}, 'revision': expected_revision + 1})
        metadata = {
            'name': f'bulk-registration-{school["school_index"]}.csv',
            'source_name': name, 'school_index': school['school_index'],
            'school': school, 'sheet': sheet, 'row_count': len(output),
            'missing_sections': missing_sections,
        }
        save_workspace(workspace_id, state, {
            '_output_authoritative': (metadata, export_frame(output, 'csv')),
        })
        return workspace_summary(state)

    if not state.get('output'):
        raise HTTPException(409, 'Generate the output preview before downloading.')
    metadata, output = read_authoritative_output(workspace_id, state)
    if metadata.get('school_index') != school['school_index']:
        raise HTTPException(409, 'The saved output belongs to another school. Generate the preview again.')
    filename = f'bulk-registration-{school["school_index"]}.{file_format}'
    try:
        exported = export_frame(output, file_format)
    except (ValueError, IllegalCharacterError) as exc:
        raise HTTPException(400, 'Could not create XLSX. Check for invalid spreadsheet characters or download CSV instead.') from exc
    media_type = ('text/csv' if file_format == 'csv' else
                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    return Response(exported, media_type=media_type,
                    headers={'Content-Disposition': f'attachment; filename="{filename}"',
                             'Cache-Control': 'no-store',
                             'X-Workspace-Revision': str(state['revision'])})
