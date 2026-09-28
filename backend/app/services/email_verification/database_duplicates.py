"""Match preview emails to addresses returned from users.user_email."""


def find_database_duplicates(emails, existing_emails):
    existing_keys = {str(email).strip().casefold() for email in existing_emails}
    return sorted({
        str(email).strip()
        for email in emails
        if str(email).strip().casefold() in existing_keys
    })

# Purpose: Match preview emails to addresses returned from users.user_email.
# Its public interface includes find_database_duplicates.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.bulk_registration.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
