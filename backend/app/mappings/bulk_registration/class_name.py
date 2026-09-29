"""Map source class names to bulk-registration class identifiers."""

CLASS_NUMBERS = {
    'class i': '0',
    'class ii': '1',
    'class iii': '2',
    'class iv': '3',
    'class v': '4',
    'class vi': '5',
    'class vii': '6',
    'class viii': '7',
    'class ix': '8',
    'class x': '9',
    'class xi': '10',
    'class xii': '11',
    'other': '12',
    'nursery': '13',
    'lkg': '14',
    'ukg': '15',
    'passed out': '16',
    'kg': '17',
    'pre nursery': '18',
    'pre primary': '19',
    'pre school': '20',
    'play group': '21',
}


def class_id(value):
    """Return the class ID for a class name, or blank for an unknown value."""
    return CLASS_NUMBERS.get(str(value).strip().casefold(), '')


def missing_class_records(output):
    """Backward-compatible entry point for class preview sanity."""
    from app.services.bulk_reg_preview_sanity.class_number import missing_class_records as check
    return check(output)

# Purpose: Map source class names to bulk-registration class identifiers.
# Its public interface includes class_id, missing_class_records.
# It keeps declarative conversion rules separate from orchestration and HTTP code.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.mappings.bulk_registration.__init__, app.routes.bulk_registration.compatibility, app.routes.bulk_registration.conversion_routes.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
