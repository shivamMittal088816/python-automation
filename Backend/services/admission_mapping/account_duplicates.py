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
