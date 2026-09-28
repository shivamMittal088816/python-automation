"""Values that override corresponding bulk-registration input columns."""

FIXED_VALUES = {
    'Category': '0',
    'USER TYPE': 'Student',
    'user_subscription_date': '2026-04-01 00:00:00',
    'user_package': '14',
    'user_activated': '1',
    'user_subscribed': '1',
    'year': '2026',
}

# Purpose: Values that override corresponding bulk-registration input columns.
# It primarily establishes package exports, constants, or module-level configuration.
# It keeps declarative conversion rules separate from orchestration and HTTP code.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.mappings.bulk_registration.__init__.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
