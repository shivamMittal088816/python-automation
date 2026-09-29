"""Generated-preview sanity rules for the FULL NAME field."""

from .common import source_rows


def blank_full_name_records(frame):
    """Return students with empty or whitespace-only full names."""
    blank = frame['FULL NAME'].fillna('').astype(str).str.strip().eq('')
    rows = source_rows(frame)
    return [
        {
            'row_number': int(rows[position]),
            'admission_number': str(row['admission_number']),
            'first_name': str(row['FIRST NAME']),
            'last_name': str(row['LAST NAME']),
            'status': 'Needs full name',
        }
        for position, (_, row) in enumerate(frame.iterrows()) if blank.iloc[position]
    ]
