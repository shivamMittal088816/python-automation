"""Check optional input houses against the dump's house names."""
from .common import CheckResult


def house_columns(frame):
    return [column for column in frame.columns
            if str(column).strip().casefold() == 'house']


def check(records, columns, houses):
    known = {str(value).strip().casefold() for value in houses if value is not None}
    failed = frozenset(
        position for position, record in enumerate(records)
        if any(record[column] and record[column].casefold() not in known
               for column in columns)
    )
    return CheckResult('house', 'House exists in dump',
                       'House not found in dump; insert the house', failed)
