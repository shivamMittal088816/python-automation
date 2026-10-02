"""Assemble focused bulk-registration route modules."""
from fastapi import APIRouter, Depends
from app.api.session_cookie import verify_origin

from app.routes.bulk_registration import conversion_routes, file_routes, school_routes, workspace_routes
from app.routes.bulk_registration.compatibility import clear_workspace, convert_file, load_path, upload_file
from app.routes.bulk_registration.file_reading import preview_file
from app.routes.bulk_registration.models import FilePathInput
from app.routes.bulk_registration.school_routes import get_school


router = APIRouter(prefix='/bulk-reg', tags=['Bulk registration'], dependencies=[Depends(verify_origin)])
for child in (workspace_routes.router, file_routes.router, school_routes.router, conversion_routes.router):
    router.include_router(child)

__all__ = [
    'FilePathInput', 'clear_workspace', 'convert_file', 'get_school',
    'load_path', 'preview_file', 'router', 'upload_file',
]

# Purpose: Assemble focused bulk-registration route modules.
# It primarily establishes package exports, constants, or module-level configuration.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: Python imports this package marker while resolving its child modules.
# Consumers normally import the focused modules inside this package directly.
# Tests and higher-level workflows exercise this behavior through its public callers.
