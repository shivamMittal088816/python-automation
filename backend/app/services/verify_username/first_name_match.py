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

# Purpose: Verify that removing a username's numeric suffix yields its first name.
# Its public interface includes find_first_name_mismatches.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.bulk_registration.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
