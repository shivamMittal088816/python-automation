"""Verify that removing a username's numeric suffix yields its first name."""
import re


def find_first_name_mismatches(records):
    mismatches = []
    for _, row in records.iterrows():
        username = str(row['user_name']).strip()
        expected = str(row['FIRST NAME']).strip().lower()
        suffix = re.fullmatch(r'(.+?)(\d+)', username)
        actual = suffix.group(1).lower() if suffix else username.lower()
        if not expected or suffix is None or actual != expected:
            mismatches.append({
                'first_name': str(row['FIRST NAME']),
                'username': username,
                'username_prefix': actual,
            })
    return mismatches
