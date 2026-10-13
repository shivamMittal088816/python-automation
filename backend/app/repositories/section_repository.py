"""Read the canonical section identifiers used by bulk registration."""
from app.queries import load_query


SECTIONS_QUERY = load_query('sections.sql')


def fetch_sections():
    from app.config.database import engine
    with engine.connect() as connection:
        rows = connection.execute(SECTIONS_QUERY).all()
    return [(row[0], row[1]) for row in rows]

# Purpose: Read the canonical section identifiers used by bulk registration.
# Its public interface includes fetch_sections.
# It isolates SQL and database access from services and route handlers.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.conversion_routes.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
