"""Generated-preview sanity rules for the FIRST NAME field."""

from .common import source_rows


def invalid_first_name_records(frame):
    """Return rows whose first name is not made solely of ASCII letters."""
    first_names = frame['FIRST NAME'].fillna('').astype(str)
    valid = first_names.str.fullmatch(r'[A-Za-z]+')
    rows = source_rows(frame)
    records = []
    for position, (_, row) in enumerate(frame.iterrows()):
        if valid.iloc[position]:
            continue
        first_name = first_names.iloc[position]
        if not first_name.strip():
            status = 'First name is blank'
        elif any(character.isspace() for character in first_name):
            status = 'Spaces are not allowed'
        else:
            status = 'Only A-Z and a-z are allowed'
        records.append({
            'row_number': int(rows[position]),
            'first_name': first_name,
            'last_name': str(row['LAST NAME']),
            'full_name': str(row['FULL NAME']),
            'admission_number': str(row['admission_number']),
            'status': status,
        })
    return records
