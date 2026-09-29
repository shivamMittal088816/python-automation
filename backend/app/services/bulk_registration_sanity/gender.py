"""Require a gender recognized by the bulk-registration mapping."""
from app.mappings.bulk_registration.gender import gender_number

from .common import CheckResult


def check(records):
    failed = frozenset(position for position, record in enumerate(records)
                       if not gender_number(record.get('GENDER', '')))
    return CheckResult('gender', 'Gender is Male, Female or Others',
                       'Gender missing or invalid: use Male, Female or Others', failed)
