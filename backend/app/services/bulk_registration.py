"""Fixed output schema and conversion rules, independent of mapping state."""
from io import BytesIO
from itertools import chain

import pandas as pd
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from sqlalchemy import text

from app.mappings.bulk_registration import FIXED_VALUES, OUTPUT_HEADERS, class_id, gender_number
from app.mappings.bulk_registration.password import generate_password


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
