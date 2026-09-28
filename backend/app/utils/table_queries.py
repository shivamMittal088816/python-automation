"""Literal table search, column resolution and pagination."""


def preview_page_bounds(total, page_size, page):
    page_count = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, page_count))
    offset = (page - 1) * page_size
    return page, page_count, offset, min(offset + page_size, total)


def search_dump(rows, query, columns=None):
    """Find literal text in any selected cell; None searches every column."""
    if not query.strip():
        return rows
    # A column group uses OR: a match in any one of its columns keeps the row.
    searchable = rows if columns is None else rows.loc[:, columns]
    matches = searchable.apply(
        lambda column: column.astype(str).str.contains(query.strip(), case=False, regex=False),
    ).any(axis=1)
    return rows.loc[matches]


def find_dump_column(frame, aliases):
    """Resolve dump headers regardless of case, whitespace, or underscores."""
    # Normalize dump header spelling for comparison; original column labels remain available.
    def normalize(value):
        return "".join(str(value).lower().replace("_", "").split())

    columns = {normalize(column): column for column in frame.columns}
    return next((columns[normalize(alias)] for alias in aliases
                 if normalize(alias) in columns), None)

# Purpose: Literal table search, column resolution and pagination.
# Its public interface includes preview_page_bounds, search_dump, find_dump_column.
# It supplies reusable helpers without owning endpoint or workflow state.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.api.file_workflow_configuration, app.api.file_workflow_helpers, app.api.file_workflow_responses.
# It also has 1 additional direct importer in the backend.
# Tests and higher-level workflows exercise this behavior through its public callers.
