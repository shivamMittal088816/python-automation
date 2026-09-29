"""Generated-preview sanity and identifier mapping for the Section field."""

from app.mappings.bulk_registration.section import normalize_section

from .common import source_rows, student_full_name


def apply_section_ids(frame, database_sections):
    """Populate section_index and return rows that do not resolve to a database ID."""
    lookup = {}
    for section_id, section_name in database_sections:
        normalized = normalize_section(section_name)
        index = '' if section_id is None else str(section_id).strip()
        if normalized and index:
            lookup.setdefault(normalized, index)

    missing = []
    indexes = []
    rows = source_rows(frame)
    for position, value in enumerate(frame['Section']):
        display = ' '.join(str(value or '').split())
        normalized = normalize_section(display)
        indexes.append(lookup.get(normalized, ''))
        if normalized not in lookup:
            row = frame.iloc[position]
            missing.append({
                'section': display,
                'full_name': student_full_name(row),
                'row_number': int(rows[position]),
                'status': 'Section is blank' if not display else 'Section not exist',
            })
    frame['section_index'] = indexes
    return missing
