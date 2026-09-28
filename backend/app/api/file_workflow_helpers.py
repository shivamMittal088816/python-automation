"""Compatibility imports for shared table and workbook operations."""
from app.utils.workbook_operations import (
    move_students,
    remove_original_columns,
    convert_dump,
)
from app.utils.table_queries import (
    preview_page_bounds,
    search_dump,
    find_dump_column,
)
from app.utils.school_statistics import (
    inferred_school_index,
    class_section_table,
    school_class_statistics,
    dump_overview,
)

__all__ = ['move_students', 'remove_original_columns', 'preview_page_bounds', 'search_dump', 'find_dump_column', 'convert_dump', 'inferred_school_index', 'class_section_table', 'school_class_statistics', 'dump_overview']


# Purpose: Provides a compatibility import surface for shared workbook and table helpers.
# It re-exports student movement, column cleanup, dump conversion, search, and paging.
# It also exposes column discovery and school/class/section statistics functions.
# The implementations remain in focused app.utils modules rather than being duplicated.
# __all__ documents and restricts the names intended for compatibility consumers.
# Used by: legacy callers can retain one stable file_workflow_helpers import path.
# Backend dump-overview tests import the statistics helpers through this module.
# New production modules generally import the focused utility modules directly.
