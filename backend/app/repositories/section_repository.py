"""Read the canonical section identifiers used by bulk registration."""
from sqlalchemy import text


def fetch_sections():
    from app.config.database import engine
    with engine.connect() as connection:
        rows = connection.execute(text(
            'SELECT section_id, section FROM users_sections WHERE section IS NOT NULL'
        )).all()
    return [(row[0], row[1]) for row in rows]
