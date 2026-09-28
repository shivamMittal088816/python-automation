"""Match preview emails to addresses returned from users.user_email."""


def find_database_duplicates(emails, existing_emails):
    existing_keys = {str(email).strip().casefold() for email in existing_emails}
    return sorted({
        str(email).strip()
        for email in emails
        if str(email).strip().casefold() in existing_keys
    })
