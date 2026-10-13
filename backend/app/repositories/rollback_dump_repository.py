"""Fetch the rollback dump for a verified school."""

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import text


QUERY_PATH = Path(__file__).resolve().parents[1] / 'queries' / 'rollback_school_dump.sql'
ROLLBACK_DUMP_QUERY = text(QUERY_PATH.read_text(encoding='utf-8'))


@contextmanager
def stream_rollback_dump(school_index):
    """Yield dump columns and a database-backed row iterator."""
    school_index = str(school_index).strip()
    if not school_index or not school_index.isascii() or not school_index.isdecimal():
        raise ValueError('Enter a numeric school index.')

    from app.config.database import engine
    with engine.connect() as connection:
        result = connection.execution_options(stream_results=True).execute(
            ROLLBACK_DUMP_QUERY, {'school_index': school_index},
        )
        columns = list(result.keys())
        rows = (
            ['' if value is None else str(value) for value in row]
            for row in result
        )
        yield columns, rows


def fetch_rollback_dump(school_index):
    """Compatibility helper that materializes the streamed dump."""
    with stream_rollback_dump(school_index) as (columns, rows):
        return {'columns': columns, 'rows': list(rows)}
