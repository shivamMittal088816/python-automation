"""Find account identifiers assigned to multiple matched rows."""

from collections import Counter

import pandas as pd


def duplicate_account_positions(groups, usernames, user_ids):
    def identifier(value):
        return str(value).strip() if pd.notna(value) else ""

    accounts = list(zip(groups, usernames, user_ids))
    duplicates = set()
    for column in (1, 2):
        counts = Counter(identifier(row[column]) for row in accounts
                         if row[0] == "Matched" and identifier(row[column]))
        duplicates.update(position for position, row in enumerate(accounts)
                          if row[0] == "Matched" and counts[identifier(row[column])] > 1)
    return duplicates

# Purpose: Find account identifiers assigned to multiple matched rows.
# Its public interface includes duplicate_account_positions.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.admission_mapping.admission_duplicate_checks, app.services.shared_mapping.mapping_username_uniqueness.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
