"""Authoritative header policy for rollback input files."""

ROLLBACK_ALLOWED_HEADERS = (
    'FIRST NAME',
    'LAST NAME',
    'FULL NAME',
    'Class Number',
    'CLASS',
    'Section',
    'EMAIL',
    'PASSWORD',
    'CONTACT',
    'GENDER',
    'Gender Number',
    'Category',
    'USER TYPE',
    'SCHOOL',
    'School Number',
    'user_subscription_date',
    'user_package',
    'user_activated',
    'user_subscribed',
    'user_name',
    'admission_number',
    'section_index',
    'year',
    'user_id',
)
ROLLBACK_REQUIRED_HEADERS = ('user_id',)


def validate_rollback_headers(columns):
    """Validate exact, case-sensitive header names after trimming whitespace."""
    headers = [str(column).strip() for column in columns]
    allowed = set(ROLLBACK_ALLOWED_HEADERS)
    unsupported = list(dict.fromkeys(header for header in headers if header not in allowed))
    missing = [header for header in ROLLBACK_REQUIRED_HEADERS if header not in headers]
    valid = not missing and not unsupported

    if valid:
        message = 'Sanity check passed. All headers are allowed and user_id is present.'
    else:
        problems = []
        if missing:
            problems.append(f'missing required header(s): {", ".join(missing)}')
        if unsupported:
            problems.append(f'unsupported header(s): {", ".join(unsupported)}')
        message = f'Sanity check failed — {"; ".join(problems)}.'

    return {
        'valid': valid,
        'missing_headers': missing,
        'unsupported_headers': unsupported,
        'message': message,
    }
