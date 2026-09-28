"""Map source gender labels to bulk-registration numeric identifiers."""

GENDER_NUMBERS = {
    'male': '1',
    'female': '2',
    'others': '3',
}


def gender_number(value):
    """Return the numeric gender identifier, or blank for an unknown value."""
    return GENDER_NUMBERS.get(str(value).strip().casefold(), '')


def missing_gender_records(output):
    """Describe students whose gender is blank or has no predefined mapping."""
    missing = []
    source_rows = output.attrs.get('source_row_numbers', range(2, len(output) + 2))
    for position, value in enumerate(output['GENDER']):
        display = str(value).strip()
        if gender_number(display) == '':
            row = output.iloc[position]
            full_name = str(row['FULL NAME']).strip() or ' '.join(
                part for part in (str(row['FIRST NAME']).strip(), str(row['LAST NAME']).strip()) if part
            )
            missing.append({
                'gender': display,
                'full_name': full_name,
                'admission_number': str(row['admission_number']),
                'row_number': int(source_rows[position]),
                'status': 'Gender is blank' if not display else 'Gender not exist',
            })
    return missing
