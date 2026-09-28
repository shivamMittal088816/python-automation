"""Find usernames that occur more than once in the generated preview."""


def find_preview_duplicates(usernames):
    normalized = usernames.astype(str).str.strip()
    duplicate_mask = normalized.str.casefold().duplicated(keep=False)
    return sorted(set(normalized.loc[duplicate_mask].tolist()))

# Purpose: Find usernames that occur more than once in the generated preview.
# Its public interface includes find_preview_duplicates.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.bulk_registration.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
