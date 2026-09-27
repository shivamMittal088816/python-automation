"""Assemble focused bulk-registration route modules."""
from fastapi import APIRouter

from app.routes.bulk_registration import conversion_routes, file_routes, school_routes, workspace_routes
from app.routes.bulk_registration.compatibility import clear_workspace, convert_file, load_path, upload_file
from app.routes.bulk_registration.file_reading import preview_file
from app.routes.bulk_registration.models import FilePathInput
from app.routes.bulk_registration.school_routes import get_school


router = APIRouter(prefix='/bulk-reg', tags=['Bulk registration'])
for child in (workspace_routes.router, file_routes.router, school_routes.router, conversion_routes.router):
    router.include_router(child)

__all__ = [
    'FilePathInput', 'clear_workspace', 'convert_file', 'get_school',
    'load_path', 'preview_file', 'router', 'upload_file',
]
