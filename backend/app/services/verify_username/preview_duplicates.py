"""Find usernames that occur more than once in the generated preview."""


def find_preview_duplicates(usernames):
    normalized = usernames.astype(str).str.strip()
    duplicate_mask = normalized.str.casefold().duplicated(keep=False)
    return sorted(set(normalized.loc[duplicate_mask].tolist()))
