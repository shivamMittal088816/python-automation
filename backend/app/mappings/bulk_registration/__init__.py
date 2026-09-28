"""Bulk-registration output schema and value mappings."""

from app.mappings.bulk_registration.class_name import class_id
from app.mappings.bulk_registration.fixed_values import FIXED_VALUES
from app.mappings.bulk_registration.gender import gender_number
from app.mappings.bulk_registration.output_schema import OUTPUT_HEADERS

__all__ = ['FIXED_VALUES', 'OUTPUT_HEADERS', 'class_id', 'gender_number']

# Purpose: Bulk-registration output schema and value mappings.
# It primarily establishes package exports, constants, or module-level configuration.
# It keeps declarative conversion rules separate from orchestration and HTTP code.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: Python imports this package marker while resolving its child modules.
# Consumers normally import the focused modules inside this package directly.
# Tests and higher-level workflows exercise this behavior through its public callers.
