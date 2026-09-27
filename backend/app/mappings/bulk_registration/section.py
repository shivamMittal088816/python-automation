"""Match input section names to database section identifiers."""


def normalize_section(value):
    return ' '.join(str(value or '').split()).casefold()


def apply_section_ids(output, database_sections):
    """Populate section_index and return distinct nonblank section names not found."""
    lookup = {}
    for section_id, section_name in database_sections:
        normalized = normalize_section(section_name)
        if normalized:
            lookup.setdefault(normalized, str(section_id))

    missing = {}
    indexes = []
    for value in output['Section']:
        display = ' '.join(str(value or '').split())
        normalized = normalize_section(display)
        indexes.append(lookup.get(normalized, ''))
        if normalized and normalized not in lookup:
            missing.setdefault(normalized, display)
    output['section_index'] = indexes
    return sorted(missing.values(), key=str.casefold)
