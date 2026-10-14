"""Normalization rules for rollback user IDs stored as MySQL INT UNSIGNED."""

import re


MYSQL_UNSIGNED_INT_MAX = 4_294_967_295


def normalize_user_id(value):
    """Return the canonical integer ID or raise ValueError for invalid input."""
    text = str(value).strip()
    if re.fullmatch(r'[0-9]+', text) is None:
        raise ValueError('user_id must contain digits only')

    user_id = int(text)
    if user_id > MYSQL_UNSIGNED_INT_MAX:
        raise ValueError(
            f'user_id must be between 0 and {MYSQL_UNSIGNED_INT_MAX}'
        )
    return user_id
