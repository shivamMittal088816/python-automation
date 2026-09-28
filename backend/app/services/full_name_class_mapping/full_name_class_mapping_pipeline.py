"""Coordinate concatenated full name and class mapping."""
from .full_name_class_dump_lookup import build_full_name_class_lookup
from .full_name_class_row_classification import classify_full_name_class_rows
from .full_name_class_result_exports import build_full_name_class_exports


def map_by_full_name_class(school, dump, name_column, class_column):
    lookup = build_full_name_class_lookup(dump)
    rows, groups = classify_full_name_class_rows(school, lookup, name_column, class_column)
    return build_full_name_class_exports(rows, groups)

# Purpose: Coordinate concatenated full name and class mapping.
# Its public interface includes map_by_full_name_class.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.full_name_class_mapping.full_name_class_file_mapping.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
