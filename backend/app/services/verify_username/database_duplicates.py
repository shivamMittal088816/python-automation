"""Match generated usernames to usernames returned from the users table."""


def find_database_duplicates(usernames, existing_usernames):
    existing_keys = {str(username).strip().casefold() for username in existing_usernames}
    return sorted({
        str(username).strip()
        for username in usernames
        if str(username).strip().casefold() in existing_keys
    })

# Purpose: Match generated usernames to usernames returned from the users table.
# Its public interface includes find_database_duplicates.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.bulk_registration.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
