"""Canonical bulk-registration output column order."""

OUTPUT_HEADERS = [
    'FIRST NAME', 'LAST NAME', 'FULL NAME', 'Class Number', 'CLASS', 'Section',
    'EMAIL', 'PASSWORD', 'CONTACT', 'GENDER', 'Gender Number', 'Category',
    'USER TYPE', 'SCHOOL', 'School Number', 'user_subscription_date',
    'user_package', 'user_activated', 'user_subscribed', 'user_name',
    'admission_number', 'house', 'section_index', 'year',
]

# Purpose: Canonical bulk-registration output column order.
# It primarily establishes package exports, constants, or module-level configuration.
# It keeps declarative conversion rules separate from orchestration and HTTP code.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.mappings.bulk_registration.__init__.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
