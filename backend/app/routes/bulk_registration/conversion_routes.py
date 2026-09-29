"""Paginated output preview and CSV/XLSX download endpoint."""
from io import BytesIO
from math import ceil
from typing import Annotated, Literal

import pandas as pd
from fastapi import APIRouter, File, Form, Header, HTTPException, Request, Response, UploadFile
from openpyxl.utils.exceptions import IllegalCharacterError
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.section_repository import fetch_sections
from app.repositories.email_repository import fetch_existing_emails
from app.repositories.username_repository import fetch_available_usernames, fetch_existing_usernames
from app.routes.bulk_registration.file_reading import read_frame
from app.routes.bulk_registration.school_routes import get_school
from app.routes.bulk_registration.workspace_access import require_revision, workspace_for, workspace_summary
from app.services.bulk_registration import (
    apply_available_usernames, convert_frame, export_frame, fill_blank_emails,
    refresh_generated_emails,
)
from app.services.bulk_reg_preview_sanity import (
    apply_section_ids, blank_full_name_records, build_review_records,
    duplicate_email_records, invalid_email_records, invalid_first_name_records,
    missing_class_records, missing_gender_records,
)
from app.services.bulk_registration_storage import read_snapshot, save_workspace, workspace_locked
from app.services.bulk_reg_final_verification import (
    repair_conflicting_usernames, verify_final_output,
)


router = APIRouter()
OUTPUT_PREVIEW_PAGE_SIZE = 20
Revision = Annotated[int, Header(alias='X-Workspace-Revision', ge=0)]


def paginated_summary(
    name, output, school, sheet, page, missing_sections,
    missing_classes=None, missing_genders=None, duplicate_emails=None,
):
    if page < 1:
        raise HTTPException(400, 'Preview page must be 1 or greater.')
    total_pages = max(1, ceil(len(output) / OUTPUT_PREVIEW_PAGE_SIZE))
    if page > total_pages:
        raise HTTPException(400, 'The requested preview page does not exist.')
    start = (page - 1) * OUTPUT_PREVIEW_PAGE_SIZE
    preview = output.iloc[start:start + OUTPUT_PREVIEW_PAGE_SIZE]
    class_records = missing_class_records(output) if missing_classes is None else missing_classes
    gender_records = missing_gender_records(output) if missing_genders is None else missing_genders
    email_records = duplicate_email_records(output) if duplicate_emails is None else duplicate_emails
    invalid_emails = invalid_email_records(output)
    first_name_records = invalid_first_name_records(output)
    full_name_records = blank_full_name_records(output)
    review_records = build_review_records(
        output,
        first_names=first_name_records,
        full_names=full_name_records,
        sections=missing_sections,
        classes=class_records,
        genders=gender_records,
        duplicate_emails=email_records,
        invalid_emails=invalid_emails,
    )
    return {'name': name, 'row_count': len(output), 'columns': list(output.columns),
            'rows': preview.values.tolist(), 'school': school, 'page': page,
            'page_size': OUTPUT_PREVIEW_PAGE_SIZE, 'total_pages': total_pages, 'sheet': sheet,
            'missing_sections': missing_sections,
            'missing_classes': class_records,
            'missing_genders': gender_records,
            'duplicate_email_records': email_records,
            'invalid_email_records': invalid_emails,
            'invalid_first_name_records': first_name_records,
            'blank_full_name_records': full_name_records,
            'review_records': review_records}


def read_authoritative_output(workspace_id, state):
    reference = state.get('outputs', {}).get('authoritative')
    metadata, data = read_snapshot(workspace_id, reference)
    try:
        output = pd.read_csv(BytesIO(data), dtype=str, keep_default_na=False)
    except Exception as exc:
        raise HTTPException(409, 'Saved bulk registration output is unreadable. Generate the preview again.') from exc
    if 'source_row_numbers' in metadata:
        output.attrs['source_row_numbers'] = metadata['source_row_numbers']
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
        metadata.get('missing_classes'),
        metadata.get('missing_genders'),
        metadata.get('duplicate_email_records', []),
    )
    visible_state = dict(state)
    visible_state['output'] = summary
    return workspace_summary(visible_state)


@router.post('/output/verify')
@workspace_locked
def verify_bulk_registration_output(
    request: Request, response: Response, expected_revision: Revision,
):
    workspace_id, state = workspace_for(request, response)
    require_revision(state, expected_revision)
    if not state.get('output'):
        raise HTTPException(409, 'Generate the output preview before running bulk-reg verification.')
    metadata, output = read_authoritative_output(workspace_id, state)
    previous_usernames = output['user_name'].fillna('').astype(str).str.strip().tolist()
    try:
        username_changes = repair_conflicting_usernames(
            output, fetch_available_usernames, fetch_existing_usernames,
        )
        current_usernames = output['user_name'].fillna('').astype(str).str.strip().tolist()
        changed_positions = {
            position for position, (previous, current) in
            enumerate(zip(previous_usernames, current_usernames))
            if previous != current
        }
        generated_email_positions = set(metadata.get('generated_email_positions', []))
        refresh_generated_emails(
            output, (metadata.get('school') or {}).get('school_name', ''),
            changed_positions & generated_email_positions,
        )
        usernames = output['user_name'].fillna('').astype(str).str.strip().tolist()
        emails = output['EMAIL'].fillna('').astype(str).str.strip().tolist()
        existing_usernames = fetch_existing_usernames(usernames)
        existing_emails = fetch_existing_emails(emails)
    except SQLAlchemyError as exc:
        raise HTTPException(
            503, 'Could not verify usernames and emails against the database. '
                 'Check the database connection and try again.'
        ) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

    verification = verify_final_output(output, existing_usernames, existing_emails)
    if username_changes:
        page = int(state.get('output', {}).get('page', 1))
        state['output'] = paginated_summary(
            metadata.get('source_name', ''), output, metadata.get('school'),
            metadata.get('sheet'), page, metadata.get('missing_sections', []),
            metadata.get('missing_classes'), metadata.get('missing_genders'),
            metadata.get('duplicate_email_records', []),
        )
        state['revision'] = int(state.get('revision', 0)) + 1
        save_workspace(workspace_id, state, {
            '_output_authoritative': (metadata, export_frame(output, 'csv')),
        })
    return {
        'workspace': workspace_summary(state),
        'verification': verification,
        'username_changes': username_changes,
    }


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
            input_duplicate_emails = duplicate_email_records(output)
            first_names = output.loc[
                output['FIRST NAME'].astype(str).str.strip().ne(''), 'FIRST NAME'
            ].tolist()
            apply_available_usernames(output, fetch_available_usernames(first_names))
            generated_email_positions = [
                position for position, value in enumerate(output['EMAIL'])
                if str(value).strip() == '' and str(output.iloc[position]['user_name']).strip()
            ]
            fill_blank_emails(output, school['school_name'])
        except SQLAlchemyError as exc:
            raise HTTPException(503, 'Could not verify sections or allocate usernames. Check the database connection and try again.') from exc
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        summary = paginated_summary(
            name, output, school, sheet, page, missing_sections,
            duplicate_emails=input_duplicate_emails,
        )
        state.update({'school_index': school['school_index'], 'school': school,
                      'output': summary, 'outputs': {}, 'revision': expected_revision + 1})
        metadata = {
            'name': f'bulk-registration-{school["school_index"]}.csv',
            'source_name': name, 'school_index': school['school_index'],
            'school': school, 'sheet': sheet, 'row_count': len(output),
            'missing_sections': missing_sections,
            'missing_classes': summary['missing_classes'],
            'missing_genders': summary['missing_genders'],
            'duplicate_email_records': input_duplicate_emails,
            'source_row_numbers': output.attrs['source_row_numbers'],
            'generated_email_positions': generated_email_positions,
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

# Purpose: Paginated output preview and CSV/XLSX download endpoint.
# Its public interface includes paginated_summary, read_authoritative_output, get_output_page, verify_bulk_registration_output, convert_workspace_file.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.__init__, app.routes.bulk_registration.compatibility.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
