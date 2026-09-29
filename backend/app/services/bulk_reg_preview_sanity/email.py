"""Generated-preview sanity rules for duplicate EMAIL values."""

from app.services.bulk_registration_sanity.email import EMAIL_PATTERN

from .common import source_rows, student_full_name


def duplicate_email_records(frame):
    """Return duplicate nonblank emails present before output email generation."""
    emails = frame['EMAIL'].fillna('').astype(str).str.strip()
    normalized = emails.str.casefold()
    duplicate = normalized.ne('') & normalized.duplicated(keep=False)
    rows = source_rows(frame)
    return [
        {
            'row_number': int(rows[position]),
            'email': emails.iloc[position],
            'admission_number': str(row['admission_number']),
            'full_name': student_full_name(row),
            'status': 'Duplicate email in preview',
        }
        for position, (_, row) in enumerate(frame.iterrows()) if duplicate.iloc[position]
    ]


def invalid_email_records(frame):
    """Return every nonblank preview email that does not match the email pattern."""
    emails = frame['EMAIL'].fillna('').astype(str).str.strip()
    invalid = emails.ne('') & ~emails.str.fullmatch(EMAIL_PATTERN)
    rows = source_rows(frame)
    return [
        {
            'row_number': int(rows[position]),
            'email': emails.iloc[position],
            'admission_number': str(row['admission_number']),
            'full_name': student_full_name(row),
            'status': 'Email format invalid: use name@domain.com',
        }
        for position, (_, row) in enumerate(frame.iterrows()) if invalid.iloc[position]
    ]
