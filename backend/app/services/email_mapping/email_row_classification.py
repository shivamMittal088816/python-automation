"""Classify email matches and flag duplicate accounts for review."""
from collections import Counter

from app.services.shared_mapping.mapping_username_uniqueness import duplicate_matched_positions
from .email_dump_lookup import normalize


def classify_email_rows(school, lookup, email_column, name_column, school_index=None, sorted_characters=False):
    school_index = normalize(school_index)
    school_emails = [normalize(value) for value in school[email_column]]
    school_email_counts = Counter(email for email in school_emails if email)
    records = []
    for (_, row), email in zip(school.iterrows(), school_emails):
        candidates = lookup.get(email, []) if email else []
        user = candidates[0] if len(candidates) == 1 else None
        expected = ""
        status, reason = "Not Matched", "Email missing" if not email else "Email not found"
        if email and school_email_counts[email] > 1:
            status, reason = "Review", "Duplicate email in school file"
            user = None
        elif len(candidates) > 1:
            status, reason = "Review", "Email belongs to multiple dump records"
        elif user is not None:
            name = normalize(row[name_column])
            if sorted_characters:
                expected = normalize(user.get("fullname", "")) or " ".join(
                    part for part in (normalize(user.get("user_firstname", "")),
                                      normalize(user.get("user_lastname", ""))) if part)
                if name and expected and sorted(''.join(name.split())) == sorted(''.join(expected.split())):
                    status, reason = "Matched", "Pass 2: Email and sorted full name characters match"
                elif not name:
                    status, reason = "Review", "Email found; full name missing in school file"
                elif not expected:
                    status, reason = "Review", "Email found; full name missing in dump"
                else:
                    status, reason = "Review", "Email found; full name is different"
            else:
                expected = normalize(user.get("user_firstname", ""))
                if name and expected and name == expected:
                    if len(name.replace(".", "").strip()) == 1:
                        status, reason = "Review", "First name matches but is only 1 character"
                    else:
                        status, reason = "Matched", "Email and first name match"
                elif not name:
                    status, reason = "Review", "Email found; first name missing in school file"
                elif not expected:
                    status, reason = "Review", "Email found; first name missing in dump"
                else:
                    status, reason = "Review", "Email found; first name is different"
        if status == "Matched":
            matched_name = "full name" if sorted_characters else "first name"
            dump_school = normalize(user.get("user_edu_school"))
            if not school_index or school_index == "null":
                status, reason = "Review", f"Email and {matched_name} match; dump fetch school index missing"
            elif not dump_school or dump_school == "null":
                status, reason = "Review", f"Email and {matched_name} match; user_edu_school missing in dump"
            elif dump_school != school_index:
                status, reason = "Review", f"Email and {matched_name} match; user_edu_school differs from dump fetch school index"
        records.append({"email_mapping_email": email,
                        "email_mapping_dump_full_name": expected,
                        "email_mapping_status": f"{status} — {reason}",
                        "_email_group": status,
                        "email_mapping_user_id": str(user.get("user_id", "")) if user is not None else "",
                        "email_mapping_username": str(user.get("user_name", "")) if user is not None else ""})
    for position in duplicate_matched_positions(
            [record["_email_group"] for record in records],
            [record["email_mapping_username"] for record in records],
            [record["email_mapping_user_id"] for record in records]):
        records[position]["_email_group"] = "Review"
        records[position]["email_mapping_status"] = (
            "Review — Duplicate username or user ID among matched students")
    return records
