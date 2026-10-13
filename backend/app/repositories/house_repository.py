"""Read house names from the configured dump database."""
from app.queries import load_query


HOUSES_QUERY = load_query('houses.sql')


def fetch_houses():
    return [name for _, name in fetch_house_ids()]


def fetch_house_ids():
    """Return database identifiers paired with their house names."""
    from app.config.database import engine
    with engine.connect() as connection:
        rows = connection.execute(HOUSES_QUERY).all()
    return [(row[0], row[1]) for row in rows]
