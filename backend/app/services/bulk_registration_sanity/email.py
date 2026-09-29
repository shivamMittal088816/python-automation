"""Find every occurrence of duplicate nonblank emails in the input file."""
from collections import Counter
import re

from .common import CheckResult


EMAIL_PATTERN = re.compile(r'^[A-Za-z0-9.!#$%&\'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\.[A-Za-z]{2,}$')


def check_format(records):
    emails = [str(record.get('EMAIL', '')).strip() for record in records]
    failed = frozenset(position for position, email in enumerate(emails)
                       if email and EMAIL_PATTERN.fullmatch(email) is None)
    return CheckResult('email_format', 'Emails use a valid name@domain format',
                       'Email format invalid: use name@domain.com', failed)


def check(records):
    emails = [str(record.get('EMAIL', '')).strip().casefold() for record in records]
    counts = Counter(email for email in emails if email)
    failed = frozenset(position for position, email in enumerate(emails)
                       if email and counts[email] > 1)
    return CheckResult('duplicate_email', 'No duplicate emails in input',
                       'Duplicate email in input file', failed)
