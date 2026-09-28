"""Find usernames shared by multiple Matched students in one mapping run."""
from app.services.admission_mapping.account_duplicates import duplicate_account_positions


def duplicate_matched_positions(groups, usernames, user_ids=None):
    if user_ids is None:
        user_ids = [""] * len(groups)
    return duplicate_account_positions(groups, usernames, user_ids)

# Purpose: Find usernames shared by multiple Matched students in one mapping run.
# Its public interface includes duplicate_matched_positions.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.email_mapping.email_row_classification, app.services.full_name_class_mapping.full_name_class_row_classification.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
