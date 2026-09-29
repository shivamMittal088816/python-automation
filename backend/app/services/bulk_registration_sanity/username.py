"""Require input usernames to be blank so bulk registration can generate them."""

from .common import CheckResult


def check(records):
    failed = frozenset(
        position for position, record in enumerate(records)
        if str(record.get('user_name', '')).strip()
    )
    return CheckResult(
        'username',
        'Username column is blank for generation',
        'Username already present in input file; leave it blank for generation',
        failed,
    )
