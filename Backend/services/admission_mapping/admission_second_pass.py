"""Retry only first-name mismatches using admission number and sorted full names."""
from io import BytesIO
import re

import pandas as pd

from Backend.api.file_workflow_helpers import find_dump_column, remove_original_columns
from Backend.services.full_name_class_mapping.full_name_class_second_round import sorted_name
from .admission_workbook import build_workbook


def map_admission_second_pass(exports, dump, name_column, admission_column, username_column):
    exports = remove_original_columns(exports)
    def read(filename):
        return pd.read_excel(BytesIO(exports[filename]['data']), dtype=str, keep_default_na=False)

    review = read('review.xlsx')
    matched = read('matched.xlsx')
    if name_column not in review or name_column.startswith('mapping_'):
        raise ValueError('Choose the full name column from the school input file.')
    fullname = find_dump_column(dump, ['fullname', 'full_name'])
    if fullname is None:
        raise ValueError('The dump must contain a fullname column for admission pass 2.')
    lookup = {}
    for row_number, (_, user) in enumerate(dump.fillna('').iterrows(), start=2):
        admission = str(user[admission_column]).strip()
        if admission:
            lookup.setdefault(admission, []).append((row_number, user))
    all_rows = pd.concat([matched, review, read('not_matched.xlsx')], ignore_index=True)
    counts = all_rows['mapping_admission_number'].astype(str).str.strip().value_counts()
    promoted = []
    for position, row in review.iterrows():
        # Match the entire pass-one reason so duplicate/manual review reasons cannot qualify.
        if not re.fullmatch(r'Review \u2014 (?:First name does not match between school and dump|admission no and firstName not match); dump row: [0-9]+', row['mapping_status']):
            continue
        admission = str(row['mapping_admission_number']).strip()
        candidates = lookup.get(admission, [])
        if not admission or counts.get(admission, 0) != 1 or len(candidates) != 1:
            continue
        row_number, user = candidates[0]
        school_name, dump_name = sorted_name(row[name_column]), sorted_name(user[fullname])
        username = str(user[username_column]).strip()
        if not school_name or not dump_name or school_name != dump_name or not username:
            continue
        promoted.append(position)
        review.at[position, 'mapping_username'] = username
        review.at[position, 'mapping_user_id'] = str(user.get('user_id', '')).strip()
        review.at[position, 'mapping_dump_row'] = str(row_number)
        review.at[position, 'mapping_dump_count'] = '1'
        review.at[position, 'mapping_status'] = 'Matched \u2014 Pass 2: Admission number and sorted full name characters match'
    if not promoted:
        return exports
    result = dict(exports)
    result['matched.xlsx'] = build_workbook(pd.concat([matched, review.loc[promoted]], ignore_index=True), 'Matched')
    result['review.xlsx'] = build_workbook(review.drop(index=promoted), 'Review')
    return result
