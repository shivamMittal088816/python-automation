"""Public imports for the reusable email mapping implementation."""
from .email_input import email_input_signature, sync_email_stage
from .email_mapping_pipeline import map_by_email

__all__ = ["email_input_signature", "sync_email_stage", "map_by_email"]

# Purpose: Public imports for the reusable email mapping implementation.
# It primarily establishes package exports, constants, or module-level configuration.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.api.file_workflow_state, app.routes.file_workflow_routes.email_mapping.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
