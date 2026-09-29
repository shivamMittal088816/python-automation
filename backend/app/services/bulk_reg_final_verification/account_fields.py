"""Blank and in-file duplicate checks for final usernames and emails."""

from .common import failed_records


def field_stages(frame, column, label):
    values = frame[column].fillna('').astype(str).str.strip()
    normalized = values.str.casefold()
    blank = normalized.eq('')
    duplicate = normalized.ne('') & normalized.duplicated(keep=False)
    return [
        {
            'id': f'blank_{column.lower()}',
            'title': f'No blank {label}s in final file',
            'passed': not blank.any(),
            'issues': [position + 1 for position, failed in enumerate(blank) if failed],
            'failed_records': failed_records(frame, blank),
        },
        {
            'id': f'duplicate_{column.lower()}',
            'title': f'No duplicate {label}s in final file',
            'passed': not duplicate.any(),
            'issues': sorted(set(values.loc[duplicate].tolist()), key=str.casefold),
            'failed_records': failed_records(frame, duplicate),
        },
    ]
