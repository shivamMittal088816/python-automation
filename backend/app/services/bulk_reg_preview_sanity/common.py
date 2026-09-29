"""Shared row metadata helpers for generated-preview sanity checks."""


def source_rows(frame):
    return frame.attrs.get('source_row_numbers', range(2, len(frame) + 2))


def student_full_name(row):
    return str(row['FULL NAME']).strip() or ' '.join(
        part for part in (
            str(row['FIRST NAME']).strip(),
            str(row['LAST NAME']).strip(),
        ) if part
    )
