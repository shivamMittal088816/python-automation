"""Generated-preview sanity rules for the Class Number field."""

from app.mappings.bulk_registration.class_name import class_id

from .common import source_rows, student_full_name


def missing_class_records(frame):
    """Return rows whose class is blank or has no stored server-side index."""
    records = []
    rows = source_rows(frame)
    for position, value in enumerate(frame['Class Number']):
        display = str(value).strip()
        if class_id(display) != '':
            continue
        row = frame.iloc[position]
        records.append({
            'class_name': display,
            'full_name': student_full_name(row),
            'admission_number': str(row['admission_number']),
            'row_number': int(rows[position]),
            'status': 'Class is blank' if not display else 'Class not stored in server',
        })
    return records
