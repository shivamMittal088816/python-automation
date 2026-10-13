"""Read the admission dump for one school from the configured MySQL database."""

import pandas as pd
from app.queries import load_query


SCHOOL_NAME_QUERY = load_query('school_name.sql')
SCHOOL_DUMP_QUERY = load_query('admission_school_dump.sql')


def _normalize_dump_rows(frame):
    """Normalize missing cells and remove records that become identical."""
    return frame.fillna("").drop_duplicates().reset_index(drop=True)


def fetch_school_dump(school_index):
    """Return text columns, preserving admission numbers with leading zeros."""
    school_index = school_index.strip()
    if not school_index or not school_index.isascii() or not school_index.isdecimal():
        raise ValueError("Enter a numeric school index.")

    # Initialize database configuration only when SQL fetching is requested.
    from app.config.database import engine

    with engine.connect() as connection:
        school_name = connection.execute(SCHOOL_NAME_QUERY, {"school_index": school_index}).scalar()
        if school_name is None or not str(school_name).strip():
            raise ValueError(f"No school found for index {school_index}.")
        result = connection.execute(SCHOOL_DUMP_QUERY, {"school_index": school_index})
        frame = pd.DataFrame(result.fetchall(), columns=list(result.keys()), dtype=str)
        # SQL DISTINCT still treats NULL and an empty string as different. Once
        # missing values are normalized for mapping, remove rows that are now
        # completely identical so the dump contains one copy of each record.
        frame = _normalize_dump_rows(frame)
        frame.attrs["school_index"] = school_index
        frame.attrs["school_name"] = str(school_name).strip()
        return frame

# Purpose: Read the admission dump for one school from the configured MySQL database.
# Its public interface includes fetch_school_dump.
# It isolates SQL and database access from services and route handlers.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.file_workflow_routes.file_inputs.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
