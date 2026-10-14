"""Preview and apply the fallback-only school rollback update."""

from datetime import date, datetime
from hashlib import sha256
import json
import re

from sqlalchemy import bindparam

from app.queries import load_query
from app.services.rollback.user_ids import normalize_user_id


FALLBACK_UPDATE_QUERY = load_query('rollback_fallback_update.sql').bindparams(
    bindparam('supplied_ids', expanding=True),
)
CANDIDATES_QUERY = load_query('rollback_candidates.sql')
LOCKED_CANDIDATES_QUERY = load_query('rollback_candidates_for_update.sql')
ROLLBACK_HASH_FIELDS = (
    'user_id',
    'user_edu_class',
    'user_package',
    'user_activated',
    'user_subscribed',
    'user_subscription_date',
)


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat(sep=' ')
    return value


def _prepared_source(frame):
    source = frame.fillna('').astype(str).apply(lambda column: column.str.strip())
    columns = {str(column).strip(): column for column in source.columns}
    return source, columns


def _supplied_user_ids(source, columns):
    """Return unique canonical IDs matching the users.user_id column type."""
    normalized = []
    seen = set()
    for row_number, value in enumerate(source[columns['user_id']], start=2):
        try:
            user_id = normalize_user_id(value)
        except ValueError as error:
            raise ValueError(f'Row {row_number}: {error}') from error
        if user_id in seen:
            raise ValueError(
                f'Row {row_number}: duplicate user_id {user_id} after numeric normalization'
            )
        seen.add(user_id)
        normalized.append(user_id)
    return normalized


def _valid_fallback_class(value):
    """Return whether a VARCHAR class can safely be decremented."""
    if value is None:
        return False
    text = str(value).strip()
    return re.fullmatch(r'[0-9]+', text) is not None and int(text) >= 1


def _plan(frame, school_index, database_rows):
    """Build summary totals and a verification hash without retaining DB rows."""
    source, columns = _prepared_source(frame)
    supplied = set(_supplied_user_ids(source, columns))
    unmatched = set(supplied)
    candidate_count = 0
    supplied_matched = 0
    invalid_class_count = 0
    hasher = sha256()
    hasher.update(json.dumps({
        'school_index': str(school_index),
        'supplied_ids': sorted(supplied),
    }, sort_keys=True, separators=(',', ':')).encode())

    for raw in database_rows:
        before = {key: _json_value(value) for key, value in dict(raw).items()}
        user_id = normalize_user_id(before['user_id'])
        candidate_count += 1
        if user_id in supplied:
            supplied_matched += 1
            unmatched.discard(user_id)
            kind = 'supplied'
        else:
            kind = 'fallback'
            if not _valid_fallback_class(before['user_edu_class']):
                invalid_class_count += 1

        # The query is ordered by user_id, making this incremental token stable.
        # Each row is hashed and then discarded instead of being kept in a plan.
        token_row = {
            'kind': kind,
            'values': [
                (field, before[field]) for field in ROLLBACK_HASH_FIELDS
            ],
        }
        hasher.update(b'\n')
        hasher.update(json.dumps(
            token_row, sort_keys=True, separators=(',', ':'), default=str,
        ).encode())

    if invalid_class_count:
        raise ValueError(
            'Rollback cannot continue: '
            f'{invalid_class_count} fallback package-14 user(s) have a blank, null, '
            'non-numeric, or zero user_edu_class. Correct those database values and '
            'analyze again.'
        )

    fallback_count = candidate_count - supplied_matched
    return {
        'school_index': str(school_index),
        'preview_token': hasher.hexdigest(),
        'supplied_count': len(supplied),
        'supplied_matched': supplied_matched,
        'fallback_count': fallback_count,
        'changed_count': fallback_count,
        'not_found_count': len(unmatched),
        'missing_ids': [],
        'changes': [],
        'updated_fields': [],
        'preview_truncated': False,
    }


def _analyze_with_connection(connection, frame, school_index, lock_rows=False):
    """Analyze candidates on a caller-owned connection, optionally locking them."""
    query = LOCKED_CANDIDATES_QUERY if lock_rows else CANDIDATES_QUERY
    rows = connection.execution_options(
        stream_results=True, yield_per=1000,
    ).execute(
        query, {'school_index': school_index},
    ).mappings()
    return _plan(frame, school_index, rows)


def preview_rollback_updates(frame, school_index):
    """Return an unlocked, constant-memory summary of current database state."""
    from app.config.database import engine
    with engine.connect() as connection:
        return _analyze_with_connection(connection, frame, school_index)


def apply_rollback_updates(frame, school_index, expected_preview_token):
    """Run one fallback update; supplied user IDs are exclusions only."""
    from app.config.database import engine

    source, columns = _prepared_source(frame)
    supplied_ids = _supplied_user_ids(source, columns)
    with engine.begin() as connection:
        current_plan = _analyze_with_connection(
            connection, frame, school_index, lock_rows=True,
        )
        if current_plan['preview_token'] != expected_preview_token:
            raise ValueError(
                'Rollback data changed after preview. '
                'Analyze the changes again before committing.'
            )
        fallback_result = connection.execute(
            FALLBACK_UPDATE_QUERY,
            {'school_index': school_index, 'supplied_ids': supplied_ids},
        )

    return {
        'supplied_count': len(supplied_ids),
        'supplied_updated': 0,
        'supplied_excluded': current_plan['supplied_matched'],
        'not_found_count': current_plan['not_found_count'],
        'fallback_updated': max(0, fallback_result.rowcount),
        'updated_fields': [],
    }
