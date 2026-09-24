"""Retry email Review name mismatches against the saved email dump."""
from io import BytesIO

import pandas as pd

from Backend.services.admission_mapping.admission_workbook import build_workbook
from .email_dump_lookup import build_email_lookup
from .email_row_classification import classify_email_rows


def map_email_second_pass(exports, dump, email_column, full_name_column, school_index):
    def read(filename):
        return pd.read_excel(BytesIO(exports[filename]['data']), dtype=str, keep_default_na=False)

    review = read('email_review.xlsx')
    if email_column not in review or full_name_column not in review:
        raise ValueError('Choose the school full name column for email pass 2.')
    eligible = review['email_mapping_status'].str.endswith('Email found; first name is different')
    candidates = review.loc[eligible]
    records = classify_email_rows(candidates, build_email_lookup(dump, 'user_email'),
                                  email_column, full_name_column, school_index, sorted_characters=True)
    promoted = []
    for position, record in zip(candidates.index, records):
        if record['_email_group'] == 'Matched':
            promoted.append(position)
            for column, value in record.items():
                if column != '_email_group':
                    review.at[position, column] = value
    result = dict(exports)
    result['email_matched.xlsx'] = build_workbook(pd.concat(
        [read('email_matched.xlsx'), review.loc[promoted]], ignore_index=True), 'Matched')
    result['email_review.xlsx'] = build_workbook(review.drop(index=promoted), 'Review')
    return result
