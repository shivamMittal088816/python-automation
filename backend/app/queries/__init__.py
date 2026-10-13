"""Load application SQL from version-controlled query files."""

from functools import lru_cache
from pathlib import Path

from sqlalchemy import text


QUERY_ROOT = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def query_source(name):
    path = QUERY_ROOT / name
    if path.parent != QUERY_ROOT or path.suffix != '.sql':
        raise ValueError('Query names must identify a SQL file in app/queries.')
    return path.read_text(encoding='utf-8').strip()


def load_query(name):
    return text(query_source(name))
