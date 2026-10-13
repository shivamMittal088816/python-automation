"""Allocate and verify bulk-registration usernames against MySQL."""
import json

from sqlalchemy import bindparam

from app.queries import load_query


AVAILABLE_USERNAMES_QUERY = load_query('available_usernames.sql')
EXISTING_USERNAMES_QUERY = load_query('existing_usernames.sql').bindparams(
    bindparam('usernames', expanding=True),
)


def fetch_available_usernames(first_names):
    prefixes = [str(name).strip().lower() for name in first_names if str(name).strip()]
    if not prefixes:
        return []

    from app.config.database import engine
    with engine.connect() as connection:
        rows = connection.execute(
            AVAILABLE_USERNAMES_QUERY, {'prefixes_json': json.dumps(prefixes)},
        ).all()
    return [str(row[0]) for row in rows]


def fetch_existing_usernames(usernames):
    values = sorted({str(username).strip().lower() for username in usernames if str(username).strip()})
    if not values:
        return set()
    from app.config.database import engine
    with engine.connect() as connection:
        rows = connection.execute(EXISTING_USERNAMES_QUERY, {'usernames': values}).all()
    return {str(row[0]) for row in rows}

# Purpose: Allocate and verify bulk-registration usernames against MySQL.
# Its public interface includes fetch_available_usernames, fetch_existing_usernames.
# It isolates SQL and database access from services and route handlers.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.compatibility, app.routes.bulk_registration.conversion_routes.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
