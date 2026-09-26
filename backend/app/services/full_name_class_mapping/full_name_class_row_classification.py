"""Classify concatenated full name and class matches and duplicate accounts."""
from app.services.shared_mapping.mapping_username_uniqueness import duplicate_matched_positions
from .full_name_class_dump_lookup import value


def classify_full_name_class_rows(school, lookup, name_column, class_column):
    rows = school.copy()
    groups = []
    keys = []
    statuses = []
    usernames = []
    user_ids = []
    for _, student in school.iterrows():
        name = value(student[name_column]).replace(" ", "")
        class_number = value(student[class_column])
        key = name + class_number if name and class_number else ""
        candidates = lookup.get(key, []) if key else []
        if not name:
            group, reason = "Not Matched", "Full name missing in school sheet"
        elif not class_number:
            group, reason = "Not Matched", "Class number missing in school sheet"
        elif len(candidates) > 1:
            group, reason = "Review", "Multiple dump records match the concatenated value"
        elif len(candidates) == 1:
            group, reason = "Matched", "One dump record matches the concatenated value"
        else:
            group, reason = "Not Matched", "No dump record matches the concatenated value"
        user = candidates[0] if group == "Matched" else None
        groups.append(group)
        keys.append(key)
        statuses.append(f"{group} — {reason}")
        usernames.append(str(user.get("user_name", "")) if user is not None else "")
        user_ids.append(str(user.get("user_id", "")) if user is not None else "")

    rows["full_name_class_generated_value"] = keys
    for position in duplicate_matched_positions(groups, usernames, user_ids):
        groups[position] = "Review"
        statuses[position] = "Review — Duplicate username or user ID among matched students"
    rows["full_name_class_status"] = statuses
    rows["full_name_class_username"] = usernames
    rows["full_name_class_user_id"] = user_ids
    return rows, groups
