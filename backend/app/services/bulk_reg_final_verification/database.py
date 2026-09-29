"""Database-conflict result stages for final usernames and emails."""

from .common import failed_records


def database_stage(frame, column, label, existing_values):
    values = frame[column].fillna('').astype(str).str.strip()
    existing = {str(value).strip().casefold() for value in existing_values}
    matched = values.str.casefold().isin(existing) & values.ne('')
    return {
        'id': f'existing_{column.lower()}',
        'title': f'No {label}s already exist in database',
        'passed': not matched.any(),
        'issues': sorted(set(values.loc[matched].tolist()), key=str.casefold),
        'failed_records': failed_records(frame, matched),
    }
