"""Coordinate email matching and workbook exports."""
from .email_dump_lookup import build_email_lookup
from .email_result_exports import build_email_exports
from .email_row_classification import classify_email_rows


def map_by_email(school, dump, email_column, dump_email_column, name_column, school_index=None):
    """Map a unique email and selected school first name to dump user_firstname."""
    lookup = build_email_lookup(dump, dump_email_column)
    school = school.copy()
    records = classify_email_rows(school, lookup, email_column, name_column, school_index)
    return build_email_exports(school, records)

# Purpose: Coordinate email matching and workbook exports.
# Its public interface includes map_by_email.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.email_mapping.email_file_mapping.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
