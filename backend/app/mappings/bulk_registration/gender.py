"""Map source gender labels to bulk-registration numeric identifiers."""

GENDER_NUMBERS = {
    'male': '1',
    'female': '2',
    'others': '3',
}


def gender_number(value):
    """Return the numeric gender identifier, or blank for an unknown value."""
    return GENDER_NUMBERS.get(str(value).strip().casefold(), '')


def missing_gender_records(output):
    """Backward-compatible entry point for gender preview sanity."""
    from app.services.bulk_reg_preview_sanity.gender import missing_gender_records as check
    return check(output)

# Purpose: Map source gender labels to bulk-registration numeric identifiers.
# Its public interface includes gender_number, missing_gender_records.
# It keeps declarative conversion rules separate from orchestration and HTTP code.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.mappings.bulk_registration.__init__, app.routes.bulk_registration.compatibility, app.routes.bulk_registration.conversion_routes.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
