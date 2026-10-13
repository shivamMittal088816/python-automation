"""Backward-compatible imports for shared tabular-file parsing."""

from app.config.settings import settings
from app.services.tabular_file import INPUT_PREVIEW_PAGE_SIZE, preview_file, read_frame


# Purpose: CSV/XLSX validation, parsing, and input previews.
# Its public interface includes read_frame and preview_file.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.__init__, app.routes.bulk_registration.compatibility, app.routes.bulk_registration.conversion_routes.
# It also has 1 additional direct importer in the backend.
# Tests and higher-level workflows exercise this behavior through its public callers.
