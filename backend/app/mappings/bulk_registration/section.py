"""Match input section names to database section identifiers."""


def normalize_section(value):
    return ' '.join(str(value or '').split()).casefold()


def apply_section_ids(output, database_sections):
    """Populate section_index and describe source rows with unknown sections."""
    lookup = {}
    for section_id, section_name in database_sections:
        normalized = normalize_section(section_name)
        if normalized:
            lookup.setdefault(normalized, str(section_id))

    missing = []
    indexes = []
    source_rows = output.attrs.get('source_row_numbers', range(2, len(output) + 2))
    for position, value in enumerate(output['Section']):
        display = ' '.join(str(value or '').split())
        normalized = normalize_section(display)
        indexes.append(lookup.get(normalized, ''))
        if normalized not in lookup:
            row = output.iloc[position]
            full_name = str(row['FULL NAME']).strip() or ' '.join(
                part for part in (str(row['FIRST NAME']).strip(), str(row['LAST NAME']).strip()) if part
            )
            missing.append({
                'section': display,
                'full_name': full_name,
                'row_number': int(source_rows[position]),
            })
    output['section_index'] = indexes
    return missing
