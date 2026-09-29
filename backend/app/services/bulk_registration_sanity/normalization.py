"""Prepare every input cell before sanity validation and preview rendering."""


def normalize_input(frame):
    """Trim surrounding whitespace while preserving internal text and column order."""
    return frame.fillna('').astype(str).apply(lambda column: column.str.strip())
