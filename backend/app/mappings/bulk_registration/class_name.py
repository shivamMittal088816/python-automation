"""Map source class names to bulk-registration class identifiers."""

CLASS_NUMBERS = {
    'class i': '0',
    'class ii': '1',
    'class iii': '2',
    'class iv': '3',
    'class v': '4',
    'class vi': '5',
    'class vii': '6',
    'class viii': '7',
    'class ix': '8',
    'class x': '9',
    'class xi': '10',
    'class xii': '11',
    'other': '12',
    'nursery': '13',
    'lkg': '14',
    'ukg': '15',
    'passed out': '16',
    'kg': '17',
    'pre nursery': '18',
    'pre primary': '19',
    'pre school': '20',
    'play group': '21',
}


def class_id(value):
    """Return the class ID for a class name, or blank for an unknown value."""
    return CLASS_NUMBERS.get(str(value).strip().casefold(), '')


def missing_class_records(output):
    """Describe students whose source class is blank or has no built-in mapping."""
    missing = []
    source_rows = output.attrs.get('source_row_numbers', range(2, len(output) + 2))
    for position, value in enumerate(output['Class Number']):
        display = str(value).strip()
        if class_id(display) == '':
            row = output.iloc[position]
            full_name = str(row['FULL NAME']).strip() or ' '.join(
                part for part in (str(row['FIRST NAME']).strip(), str(row['LAST NAME']).strip()) if part
            )
            missing.append({
                'class_name': display,
                'full_name': full_name,
                'admission_number': str(row['admission_number']),
                'row_number': int(source_rows[position]),
                'status': 'Class is blank' if not display else 'Class not exist',
            })
    return missing
