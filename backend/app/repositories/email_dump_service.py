"""Fetch users across schools using the email mapping input's email addresses."""
import pandas as pd
from sqlalchemy import bindparam, text

COLUMNS = ["user_id", "user_name", "user_edu_class", "user_edu_major", "user_firstname",
           "user_lastname", "user_package", "user_email", "user_edu_school"]
QUERY = text("""
SELECT DISTINCT u.user_id, u.user_name, u.user_edu_class, u.user_edu_major,
u.user_firstname, u.user_lastname, u.user_package, u.user_email, u.user_edu_school
FROM users u WHERE LOWER(u.user_email) IN :emails
""").bindparams(bindparam("emails", expanding=True))


# Normalize and deduplicate emails, then fetch users in parameterized batches across schools.
def fetch_email_dump(values):
    emails = sorted({str(value).strip().lower() for value in values if pd.notna(value) and str(value).strip()})
    if not emails:
        return pd.DataFrame(columns=COLUMNS)
    from app.config.database import engine
    records = []
    with engine.connect() as connection:
        for offset in range(0, len(emails), 500):
            result = connection.execute(QUERY, {"emails": emails[offset:offset + 500]})
            records.extend(result.fetchall())
    return pd.DataFrame(records, columns=COLUMNS, dtype=str).fillna("").drop_duplicates()
