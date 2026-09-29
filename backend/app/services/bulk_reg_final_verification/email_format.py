"""Email syntax validation for the final generated bulk-registration file."""

from app.services.bulk_registration_sanity.email import EMAIL_PATTERN

from .common import row_stage


def email_format_stage(frame):
    emails = frame['EMAIL'].fillna('').astype(str).str.strip()
    invalid = emails.ne('') & ~emails.str.fullmatch(EMAIL_PATTERN)
    return row_stage(
        frame, 'email_format', 'Every nonblank email uses a valid name@domain format', invalid,
    )
