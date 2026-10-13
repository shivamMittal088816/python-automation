"""Request models shared by bulk-registration routes."""
from pydantic import BaseModel

from app.schemas.file_workflow import SchoolInput


class StoredFileInput(BaseModel):
    sheet: str | None = None

# Purpose: Request models shared by bulk-registration routes.
# Its public interface includes StoredFileInput and SchoolInput.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.__init__, app.routes.bulk_registration.compatibility, app.routes.bulk_registration.file_routes.
# It also has 1 additional direct importer in the backend.
# Tests and higher-level workflows exercise this behavior through its public callers.
