"""Repeatedly regenerate final usernames until all conflicts are resolved."""
import re


def _prefix(value):
    return re.sub(r'\d+$', '', str(value).strip()).casefold()


def _replacement_usernames(frame, positions, allocate_usernames, reserved):
    names = frame.iloc[positions]['FIRST NAME'].fillna('').astype(str).str.strip().tolist()
    if any(not name for name in names):
        raise ValueError('Could not generate a replacement username for every student.')

    requested = []
    for name in names:
        prefix = name.casefold()
        reserved_count = sum(_prefix(username) == prefix for username in reserved)
        requested.extend([name] * (1 + reserved_count))
    candidates = list(allocate_usernames(requested))

    available = {}
    for candidate in candidates:
        normalized = str(candidate).strip().casefold()
        if normalized and normalized not in reserved:
            available.setdefault(_prefix(candidate), []).append(str(candidate).strip())

    replacements = []
    selected = set()
    for name in names:
        prefix = name.casefold()
        pool = available.get(prefix, [])
        candidate = next(
            (value for value in pool if value.casefold() not in selected), None,
        )
        if candidate is None:
            raise ValueError('Could not generate a replacement username for every student.')
        replacements.append(candidate)
        selected.add(candidate.casefold())
    return replacements


def repair_conflicting_usernames(frame, allocate_usernames, find_existing, max_attempts=10):
    original = frame['user_name'].fillna('').astype(str).str.strip().tolist()
    repair_positions = set()
    for _ in range(max_attempts):
        values = frame['user_name'].fillna('').astype(str).str.strip()
        normalized = values.str.casefold()
        existing = {str(value).strip().casefold() for value in find_existing(values.tolist())}
        conflicts = (
            (normalized.ne('') & normalized.duplicated(keep=False))
            | (normalized.ne('') & normalized.isin(existing))
        )
        if not conflicts.any():
            source_rows = frame.attrs.get('source_row_numbers', range(2, len(frame) + 2))
            return [
                {
                    'row_number': int(source_rows[position]),
                    'admission_number': str(frame.iloc[position]['admission_number']),
                    'first_name': str(frame.iloc[position]['FIRST NAME']),
                    'previous_username': previous,
                    'new_username': values.iloc[position],
                    'message': (
                        f'{previous or "Blank username"} conflicted, so '
                        f'{values.iloc[position]} was generated and assigned'
                    ),
                }
                for position, previous in enumerate(original)
                if previous != values.iloc[position]
            ]

        repair_positions.update(position for position, failed in enumerate(conflicts) if failed)
        positions = sorted(repair_positions)
        reserved = {
            normalized.iloc[position]
            for position in range(len(frame))
            if position not in repair_positions and normalized.iloc[position]
        }
        replacements = _replacement_usernames(
            frame, positions, allocate_usernames, reserved,
        )
        username_column = frame.columns.get_loc('user_name')
        for position, replacement in zip(positions, replacements):
            frame.iat[position, username_column] = replacement

    raise ValueError('Could not generate unique usernames after repeated verification attempts.')
