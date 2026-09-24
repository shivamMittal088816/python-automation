"""Retry first-round misses using sorted name characters and selected classes."""
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pandas as pd

from Backend.services.admission_mapping.admission_workbook import build_workbook
from Backend.services.shared_mapping.mapping_username_uniqueness import duplicate_matched_positions
from .full_name_class_dump_lookup import value
from .full_name_class_result_exports import build_full_name_class_exports


def sorted_name(item):
    """Ignore case and whitespace, preserving every other character and its count."""
    return ''.join(sorted(''.join(value(item).split())))


def class_number(item):
    text = value(item)
    if not text:
        return ''
    try:
        number = Decimal(text)
        if number.is_finite() and number == number.to_integral_value():
            return str(int(number))
    except InvalidOperation:
        pass
    return text


def map_sorted_full_name_class(school, dump, name_column, class_column):
    dump_name_column, dump_class_column = "fullname", "user_edu_class"
    for frame, columns in ((school, (name_column, class_column)),
                           (dump, (dump_name_column, dump_class_column))):
        if any(column not in frame for column in columns):
            raise ValueError('Choose valid school columns; the dump must contain fullname and user_edu_class.')
    lookup = defaultdict(list)
    for _, user in dump.iterrows():
        name = sorted_name(user[dump_name_column])
        number = class_number(user[dump_class_column])
        if name and number:
            lookup[(name, number)].append(user)

    rows = school.copy()
    groups, statuses, names, numbers, usernames, user_ids = [], [], [], [], [], []
    for _, student in school.iterrows():
        name, number = sorted_name(student[name_column]), class_number(student[class_column])
        candidates = lookup.get((name, number), []) if name and number else []
        if not name:
            group, reason = 'Not Matched', 'Full name missing in school sheet'
        elif not number:
            group, reason = 'Not Matched', 'Class number missing in school sheet'
        elif len(candidates) > 1:
            group, reason = 'Review', 'Multiple dump records match sorted full name and class'
        elif candidates:
            group, reason = 'Matched', 'One dump record matches sorted full name and class'
        else:
            group, reason = 'Not Matched', 'No dump record matches sorted full name and class'
        user = candidates[0] if group == 'Matched' else None
        groups.append(group)
        statuses.append(f'{group} — Round 2: {reason}')
        names.append(name)
        numbers.append(number)
        usernames.append(str(user.get('user_name', '')) if user is not None else '')
        user_ids.append(str(user.get('user_id', '')) if user is not None else '')
    for position in duplicate_matched_positions(groups, usernames, user_ids):
        groups[position] = 'Review'
        statuses[position] = 'Review — Round 2: Duplicate username or user ID among matched students'
    rows['full_name_class_sorted_name'] = names
    rows['full_name_class_compared_class'] = numbers
    rows['full_name_class_status'] = statuses
    rows['full_name_class_username'] = usernames
    rows['full_name_class_user_id'] = user_ids
    return build_full_name_class_exports(rows, groups)


def map_second_round(first_round, dump, name_column, class_column):
    """Keep round-one matches/reviews; replace only its Not Matched workbook."""
    def read(snapshot):
        return pd.read_excel(BytesIO(snapshot['data']), dtype=str, keep_default_na=False)

    misses = read(first_round['full_name_class_not_matched.xlsx'])
    result = map_sorted_full_name_class(misses, dump, name_column, class_column)
    for group, label in (('matched', 'Matched'), ('review', 'Review')):
        filename = f'full_name_class_{group}.xlsx'
        result[filename] = build_workbook(pd.concat(
            [read(first_round[filename]), read(result[filename])], ignore_index=True).fillna(''), label)
    return result
