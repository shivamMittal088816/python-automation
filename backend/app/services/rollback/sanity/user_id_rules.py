"""Validation rules for rollback user IDs."""

from collections import Counter

from app.services.rollback.sanity.columns import find_column
from app.services.rollback.user_ids import normalize_user_id


def evaluate_user_ids(source):
    row_count = len(source)
    positions = frozenset(range(row_count))
    column = find_column(source, 'user_id')
    if column is None:
        return {
            'missing': positions,
            'invalid': frozenset(),
            'duplicates': frozenset(),
        }

    values = source[column].tolist()
    missing = frozenset(
        position for position, value in enumerate(values) if not value
    )
    normalized = []
    invalid_positions = set()
    for position, value in enumerate(values):
        if not value:
            normalized.append(None)
            continue
        try:
            normalized.append(normalize_user_id(value))
        except ValueError:
            normalized.append(None)
            invalid_positions.add(position)

    counts = Counter(value for value in normalized if value is not None)
    duplicates = frozenset(
        position for position, value in enumerate(normalized)
        if value is not None and counts[value] > 1
    )
    return {
        'missing': missing,
        'invalid': frozenset(invalid_positions),
        'duplicates': duplicates,
    }


def append_user_id_problems(problems, position, result):
    if position in result['missing']:
        problems.append('user_id missing')
    elif position in result['invalid']:
        problems.append('user_id invalid: use digits from 0 to 4294967295 only')
    if position in result['duplicates']:
        problems.append(
            'Duplicate user_id in rollback file after numeric normalization'
        )
