"""Match generated usernames to usernames returned from the users table."""


def find_database_duplicates(usernames, existing_usernames):
    existing_keys = {str(username).strip().casefold() for username in existing_usernames}
    return sorted({
        str(username).strip()
        for username in usernames
        if str(username).strip().casefold() in existing_keys
    })
