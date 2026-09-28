"""Fixed output schema and conversion rules, independent of mapping state."""
from io import BytesIO
from itertools import chain
import re
import unicodedata

import pandas as pd
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from sqlalchemy import text

from app.mappings.bulk_registration import FIXED_VALUES, OUTPUT_HEADERS, class_id, gender_number
from app.mappings.bulk_registration.password import generate_password
from app.services.verification_records import attach_failed_records, blank_value_stage
from app.services.email_verification.database_duplicates import find_database_duplicates as find_email_database_duplicates
from app.services.email_verification.preview_duplicates import find_preview_duplicates as find_email_preview_duplicates
from app.services.verify_username.database_duplicates import find_database_duplicates
from app.services.verify_username.first_name_match import find_first_name_mismatches
from app.services.verify_username.preview_duplicates import find_preview_duplicates


class SchoolNotFoundError(ValueError):
    """The requested school identity does not exist."""


def fetch_school(school_index):
    school_index = school_index.strip()
    if not school_index or not school_index.isascii() or not school_index.isdecimal():
        raise ValueError('Enter a numeric school index.')
    from app.config.database import engine
    with engine.connect() as connection:
        row = connection.execute(
            text('SELECT school FROM users_schools WHERE school_id = :school_index'),
            {'school_index': school_index},
        ).first()
    if row is None:
        raise SchoolNotFoundError(f'No school found for index {school_index}.')
    name = str(row[0] or '').strip()
    if not name:
        raise ValueError('The school has no name stored in the database.')
    return {'school_index': school_index, 'school_name': name}


def convert_frame(frame, school):
    unknown = [str(column) for column in frame.columns if column not in OUTPUT_HEADERS]
    if unknown:
        raise ValueError('Unrecognized input headers: ' + ', '.join(unknown))
    output = frame.reindex(columns=OUTPUT_HEADERS, fill_value='').fillna('').copy()
    output['_source_row_number'] = range(2, len(output) + 2)
    first_names = output['FIRST NAME'].astype(str).str.strip().str.casefold()
    output = (output.assign(_first_name_blank=first_names.eq(''), _first_name_sort=first_names)
                    .sort_values(['_first_name_blank', '_first_name_sort'], kind='stable')
                    .drop(columns=['_first_name_blank', '_first_name_sort'])
                    .reset_index(drop=True))
    source_row_numbers = output.pop('_source_row_number').tolist()
    output.attrs['source_row_numbers'] = source_row_numbers
    output['CLASS'] = output['Class Number'].map(class_id)
    output['Gender Number'] = output['GENDER'].map(gender_number)
    # The web preview and CSV need calculated values because neither can run
    # Excel formulas. XLSX export replaces these values with the real formula.
    output['PASSWORD'] = [generate_password() for _ in range(len(output))]
    for column, value in FIXED_VALUES.items():
        output[column] = value
    output['School Number'] = school['school_index']
    output['SCHOOL'] = school['school_name']
    return output


def blank_first_name_records(frame):
    """Return identifying details for rows that cannot support username generation."""
    blank = frame['FIRST NAME'].astype(str).str.strip().eq('')
    records = []
    source_rows = frame.attrs.get('source_row_numbers', range(2, len(frame) + 2))
    for position, (_, row) in enumerate(frame.iterrows()):
        if not blank.iloc[position]:
            continue
        records.append({
            'row_number': int(source_rows[position]),
            'last_name': str(row['LAST NAME']),
            'full_name': str(row['FULL NAME']),
            'admission_number': str(row['admission_number']),
            'status': 'Provide FIRST NAME for user_name generation',
        })
    return records


def blank_full_name_records(frame):
    """Identify students with empty or whitespace-only full names."""
    blank = frame['FULL NAME'].fillna('').astype(str).str.strip().eq('')
    source_rows = frame.attrs.get('source_row_numbers', range(2, len(frame) + 2))
    return [
        {
            'row_number': int(source_rows[position]),
            'admission_number': str(row['admission_number']),
            'first_name': str(row['FIRST NAME']),
            'last_name': str(row['LAST NAME']),
            'status': 'Needs full name',
        }
        for position, (_, row) in enumerate(frame.iterrows()) if blank.iloc[position]
    ]


def apply_available_usernames(frame, usernames):
    """Assign query results to sorted nonblank first-name rows."""
    indexes = frame.index[frame['FIRST NAME'].astype(str).str.strip().ne('')]
    if len(usernames) != len(indexes):
        raise ValueError(
            'Could not allocate a username for every student. '
            'A first-name prefix may have exhausted values 001 through 1999.'
        )
    frame.loc[indexes, 'user_name'] = list(usernames)
    frame.loc[frame.index.difference(indexes), 'user_name'] = ''


def _email_component(value):
    """Keep lowercase ASCII letters and digits for generated email components."""
    normalized = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '', normalized.casefold())


def fill_blank_emails(frame, school_name):
    """Generate email addresses only where the uploaded EMAIL value is blank."""
    blank_emails = frame['EMAIL'].astype(str).str.strip().eq('')
    usernames = frame['user_name'].fillna('').map(_email_component)
    can_generate = blank_emails & usernames.ne('')
    if not can_generate.any():
        return
    domain = _email_component(school_name)
    if not domain:
        raise ValueError('The school name cannot be used to generate email addresses.')
    frame.loc[can_generate, 'EMAIL'] = usernames[can_generate] + '@' + domain + '.com'


def verify_generated_usernames(frame, existing_usernames):
    """Report preview uniqueness, database availability, and prefix integrity."""
    records = frame.loc[frame['user_name'].fillna('').astype(str).str.strip().ne('')]
    normalized = records['user_name'].astype(str).str.strip()
    preview_duplicates = find_preview_duplicates(normalized)
    existing = find_database_duplicates(normalized, existing_usernames)
    prefix_mismatches = find_first_name_mismatches(records)

    stages = [
        {
            'id': 'preview_duplicates',
            'title': 'No duplicate usernames in preview',
            'passed': not preview_duplicates,
            'issues': preview_duplicates,
        },
        {
            'id': 'database_duplicates',
            'title': 'No usernames already exist in database',
            'passed': not existing,
            'issues': existing,
        },
        {
            'id': 'first_name_match',
            'title': 'Username prefix matches first name',
            'passed': not prefix_mismatches,
            'issues': prefix_mismatches,
        },
    ]
    stages.append(blank_value_stage(frame, 'user_name', 'usernames'))
    attach_failed_records(frame, stages, 'user_name')
    return {
        'passed': all(stage['passed'] for stage in stages),
        'checked_usernames': len(frame),
        'stages': stages,
    }


def verify_output_emails(frame, existing_emails):
    """Check all output emails for missing values and duplicates."""
    emails = frame['EMAIL'].fillna('').astype(str).str.strip().str.lower()
    emails = emails.loc[emails.ne('')]
    preview_duplicates = find_email_preview_duplicates(emails)
    database_duplicates = find_email_database_duplicates(emails, existing_emails)
    stages = [
        {'id': 'preview_duplicates', 'title': 'No duplicate emails in preview',
         'passed': not preview_duplicates, 'issues': preview_duplicates},
        {'id': 'database_duplicates', 'title': 'No preview emails already exist in database',
         'passed': not database_duplicates, 'issues': database_duplicates},
    ]
    stages.append(blank_value_stage(frame, 'EMAIL', 'emails'))
    attach_failed_records(frame, stages, 'EMAIL')
    return {'passed': all(stage['passed'] for stage in stages),
            'checked_emails': len(frame), 'stages': stages}


def export_frame(frame, file_format):
    if file_format == 'csv':
        return frame.to_csv(index=False).encode('utf-8-sig')
    # Write literal text to preserve identifiers and final generated passwords.
    if len(frame) > 1_048_575:
        raise ValueError('Too many rows for XLSX. Download CSV instead.')
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet('Bulk registration')
    sheet.freeze_panes = 'A2'
    for row in chain([OUTPUT_HEADERS], frame.itertuples(index=False, name=None)):
        cells = []
        for value in row:
            cell = WriteOnlyCell(sheet, value=str(value))
            cell.data_type = 's'
            cells.append(cell)
        sheet.append(cells)
    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()
