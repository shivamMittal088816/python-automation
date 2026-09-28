"""Attach complete output records to each failed verification stage."""


def blank_value_stage(frame, column, label):
    """Check every output row for a missing or whitespace-only value."""
    blank = frame[column].fillna('').astype(str).str.strip().eq('')
    rows = [position + 1 for position, missing in enumerate(blank) if missing]
    return {'id': 'blank_values', 'title': f'No blank {label} in preview',
            'passed': not rows, 'issues': rows}


def attach_failed_records(frame, stages, column):
    keys = frame[column].fillna('').astype(str).str.strip().str.casefold()
    for stage in stages:
        if stage['id'] == 'blank_values':
            mask = keys.eq('').tolist()
        elif stage['id'] == 'first_name_match':
            mismatches = {(issue['first_name'], issue['username']) for issue in stage['issues']}
            mask = [
                (str(row['FIRST NAME']), str(row['user_name']).strip()) in mismatches
                for _, row in frame.iterrows()
            ]
        else:
            issues = {str(value).strip().casefold() for value in stage['issues']}
            mask = keys.isin(issues).tolist()
        positions = [position for position, failed in enumerate(mask) if failed]
        stage['failed_records'] = {
            'columns': ['Preview row', *frame.columns.tolist()],
            'rows': [
                [position + 1, *frame.iloc[position].fillna('').tolist()]
                for position in positions
            ],
            'row_count': len(positions),
        }
