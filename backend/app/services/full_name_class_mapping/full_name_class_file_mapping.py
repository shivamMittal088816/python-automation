"""Public imports for the reusable class and full name mapping implementation."""
from .full_name_class_file_reader import read_saved_dump
from .full_name_class_mapping_pipeline import map_by_full_name_class

__all__ = ["read_saved_dump", "map_by_full_name_class"]

# Purpose: Public imports for the reusable class and full name mapping implementation.
# It primarily establishes package exports, constants, or module-level configuration.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.file_workflow_routes.full_name_class_mapping, app.services.full_name_class_mapping.__init__.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
