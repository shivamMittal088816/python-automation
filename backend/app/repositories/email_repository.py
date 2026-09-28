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
