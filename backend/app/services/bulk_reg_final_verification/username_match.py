"""Final username-prefix to first-name verification."""

from app.services.verify_username.first_name_match import find_first_name_mismatches

from .common import failed_records


def first_name_stage(frame):
    mismatches = find_first_name_mismatches(frame)
    failed = {(issue['first_name'], issue['username']) for issue in mismatches}
    mask = [
        (str(row['FIRST NAME']), str(row['user_name']).strip()) in failed
        for _, row in frame.iterrows()
    ]
    return {
        'id': 'username_first_name_match',
        'title': 'Username without trailing digits matches lowercase first name',
        'passed': not mismatches,
        'issues': mismatches,
        'failed_records': failed_records(frame, mask),
    }
