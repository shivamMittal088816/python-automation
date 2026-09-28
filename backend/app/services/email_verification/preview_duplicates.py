"""Find email addresses repeated within the output preview."""


def find_preview_duplicates(emails):
    normalized = emails.astype(str).str.strip()
    duplicate_mask = normalized.str.casefold().duplicated(keep=False)
    return sorted(set(normalized.loc[duplicate_mask].tolist()))
