"""Check bulk-registration emails against existing users."""
from sqlalchemy import bindparam, text


def fetch_existing_emails(emails):
    values = sorted({str(email).strip().lower() for email in emails if str(email).strip()})
    if not values:
        return set()
    query = text('''SELECT u.user_email
FROM users AS u
WHERE LOWER(TRIM(u.user_email)) IN :emails''').bindparams(bindparam('emails', expanding=True))
    from app.config.database import engine
    with engine.connect() as connection:
        rows = connection.execute(query, {'emails': values}).all()
    return {str(row[0]) for row in rows}

# Purpose: Check bulk-registration emails against existing users.
# Its public interface includes fetch_existing_emails.
# It isolates SQL and database access from services and route handlers.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.conversion_routes.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
