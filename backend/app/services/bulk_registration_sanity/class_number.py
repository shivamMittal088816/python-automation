"""Require a Class Number recognized by the bulk-registration class mapping."""
from app.mappings.bulk_registration.class_name import class_id

from .common import CheckResult


def check(records):
    failed = frozenset(position for position, record in enumerate(records)
                       if class_id(record.get('Class Number', '')) == '')
    return CheckResult('class', 'Class Number matches a stored class',
                       'Class Number missing or invalid: use a stored class name', failed)
