"""Combine field-level preview failures into one student review list."""

from .common import source_rows, student_full_name


def build_review_records(
    frame, *, first_names, full_names, sections, classes, genders,
    duplicate_emails, invalid_emails,
):
    issues_by_row = {}

    def add(records, formatter):
        for record in records:
            issues_by_row.setdefault(int(record['row_number']), []).append(formatter(record))

    add(first_names, lambda record: record['status'])
    add(full_names, lambda record: 'Full name is blank')
    add(sections, lambda record: (
        'Section is blank' if not record['section']
        else f"Section not stored in server: {record['section']}"
    ))
    add(classes, lambda record: (
        'Class Number is blank' if not record['class_name']
        else f"Class not stored in server: {record['class_name']}"
    ))
    add(genders, lambda record: (
        'Gender is blank' if not record['gender']
        else f"Gender not predefined: {record['gender']}"
    ))
    add(duplicate_emails, lambda record: f"Duplicate input email: {record['email']}")
    add(invalid_emails, lambda record: f"Invalid email format: {record['email']}")

    rows = source_rows(frame)
    records = []
    for position, (_, row) in enumerate(frame.iterrows()):
        row_number = int(rows[position])
        if row_number not in issues_by_row:
            continue
        records.append({
            'row_number': row_number,
            'admission_number': str(row['admission_number']),
            'full_name': student_full_name(row),
            'issues': issues_by_row[row_number],
        })
    return records
