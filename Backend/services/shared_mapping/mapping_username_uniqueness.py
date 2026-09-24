"""Find usernames shared by multiple Matched students in one mapping run."""
from Backend.services.admission_mapping.account_duplicates import duplicate_account_positions


def duplicate_matched_positions(groups, usernames, user_ids=None):
    if user_ids is None:
        user_ids = [""] * len(groups)
    return duplicate_account_positions(groups, usernames, user_ids)
