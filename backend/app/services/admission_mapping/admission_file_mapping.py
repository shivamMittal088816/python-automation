"""Public imports for the reusable admission mapping implementation."""

from .admission_file_reader import read_file
from .admission_mapping_pipeline import map_students
from .admission_result_exports import build_exports

__all__ = ["read_file", "map_students", "build_exports"]

# Purpose: Public imports for the reusable admission mapping implementation.
# It primarily establishes package exports, constants, or module-level configuration.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.api.file_workflow_snapshots, app.routes.file_workflow_routes.admission_mapping.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
