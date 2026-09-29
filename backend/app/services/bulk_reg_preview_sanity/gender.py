"""Generated-preview sanity rules for the GENDER field."""

from app.mappings.bulk_registration.gender import gender_number

from .common import source_rows, student_full_name


def missing_gender_records(frame):
    """Return rows whose gender is blank or has no predefined server mapping."""
    records = []
    rows = source_rows(frame)
    for position, value in enumerate(frame['GENDER']):
        display = str(value).strip()
        if gender_number(display) != '':
            continue
        row = frame.iloc[position]
        records.append({
            'gender': display,
            'full_name': student_full_name(row),
            'admission_number': str(row['admission_number']),
            'row_number': int(rows[position]),
            'status': 'Gender is blank' if not display else 'Gender not predefined',
        })
    return records
