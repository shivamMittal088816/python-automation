"""Coordinate concatenated full name and class mapping."""
from .full_name_class_dump_lookup import build_full_name_class_lookup
from .full_name_class_row_classification import classify_full_name_class_rows
from .full_name_class_result_exports import build_full_name_class_exports


def map_by_full_name_class(school, dump, name_column, class_column):
    lookup = build_full_name_class_lookup(dump)
    rows, groups = classify_full_name_class_rows(school, lookup, name_column, class_column)
    return build_full_name_class_exports(rows, groups)
