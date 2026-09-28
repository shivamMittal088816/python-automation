"""Assemble mapping API routes, grouped by their purpose."""
from fastapi import APIRouter, Depends
from app.api.session_cookie import verify_origin

from app.routes.file_workflow_routes import (
    admission_mapping,
    email_mapping,
    file_downloads,
    file_inputs,
    full_name_class_mapping,
    source_files_preview,
    mapping_preview_results,
    configuration_preview,
    get_session,
    set_session,
)

router = APIRouter(prefix='/mapping', dependencies=[Depends(verify_origin)])

for workflow_router in (
    configuration_preview.router,
    set_session.router,
    get_session.router,
    file_inputs.router,
    admission_mapping.router,
    email_mapping.router,
    full_name_class_mapping.router,
    source_files_preview.router,
    mapping_preview_results.router,
    file_downloads.router,
):
    router.include_router(workflow_router)

# Purpose: Assemble mapping API routes, grouped by their purpose.
# It primarily establishes package exports, constants, or module-level configuration.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.main.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
