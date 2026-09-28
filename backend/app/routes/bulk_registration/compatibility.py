"""Pure helpers retained for tests and supported non-HTTP callers."""
from math import ceil

from fastapi import HTTPException, UploadFile
from fastapi.responses import Response

from app.config.settings import settings
from app.mappings.bulk_registration.class_name import missing_class_records
from app.mappings.bulk_registration.gender import missing_gender_records
from app.routes.bulk_registration.conversion_routes import OUTPUT_PREVIEW_PAGE_SIZE
from app.routes.bulk_registration.file_reading import preview_file, read_frame, read_path
from app.routes.bulk_registration.models import FilePathInput
from app.routes.bulk_registration.school_routes import get_school
from app.repositories.username_repository import fetch_available_usernames
from app.services.bulk_registration import (
    apply_available_usernames, blank_first_name_records, convert_frame, export_frame, fill_blank_emails,
    blank_full_name_records,
)
from app.services.bulk_registration_storage import delete_workspace


def upload_file(file: UploadFile, sheet=None):
    data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
    return preview_file(file.filename or '', data, sheet)


def load_path(payload: FilePathInput):
    name, data = read_path(payload.path)
    return preview_file(name, data, payload.sheet)


def convert_file(school_index, file_format='preview', file=None, path=None, sheet=None, page=1):
    if (file is None) == (path is None):
        raise HTTPException(400, 'Provide either an uploaded file or a file path.')
    if file is not None:
        name = file.filename or ''
        data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
    else:
        name, data = read_path(path)
    school = get_school(school_index)
    output = convert_frame(read_frame(name, data, sheet), school)
    first_names = output.loc[
        output['FIRST NAME'].astype(str).str.strip().ne(''), 'FIRST NAME'
    ].tolist()
    apply_available_usernames(output, fetch_available_usernames(first_names))
    fill_blank_emails(output, school['school_name'])
    if file_format == 'preview':
        total_pages = max(1, ceil(len(output) / OUTPUT_PREVIEW_PAGE_SIZE))
        if page < 1 or page > total_pages:
            raise HTTPException(400, 'The requested preview page does not exist.')
        start = (page - 1) * OUTPUT_PREVIEW_PAGE_SIZE
        preview = output.iloc[start:start + OUTPUT_PREVIEW_PAGE_SIZE]
        return {'name': name, 'row_count': len(output), 'columns': list(output.columns),
                'rows': preview.values.tolist(), 'school': school, 'page': page,
                'page_size': OUTPUT_PREVIEW_PAGE_SIZE, 'total_pages': total_pages,
                'missing_classes': missing_class_records(output),
                'missing_genders': missing_gender_records(output),
                'blank_first_name_records': blank_first_name_records(output),
                'blank_full_name_records': blank_full_name_records(output)}
    filename = f'bulk-registration-{school_index}.{file_format}'
    exported = export_frame(output, file_format)
    media_type = ('text/csv' if file_format == 'csv' else
                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    return Response(exported, media_type=media_type,
                    headers={'Content-Disposition': f'attachment; filename="{filename}"',
                             'Cache-Control': 'no-store'})


def clear_workspace(workspace_id):
    delete_workspace(workspace_id)

# Purpose: Pure helpers retained for tests and supported non-HTTP callers.
# Its public interface includes upload_file, load_path, convert_file, clear_workspace.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.__init__.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
