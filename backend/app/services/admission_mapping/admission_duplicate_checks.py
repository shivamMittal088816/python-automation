"""Remove identical school rows and review duplicate admissions after mapping."""


def prepare_school_rows(school, school_admission_column):
    # Remove exact whole-row duplicates before checking admission numbers.
    duplicate_rows = int(school.duplicated(keep=False).sum())
    dropped_rows = int(school.duplicated(keep="first").sum())
    school = school.drop_duplicates(keep="first")

    return school, duplicate_rows, dropped_rows


def review_duplicate_admissions(result):
    """Override every repeated nonblank admission, retaining existing review evidence."""
    admissions = result["mapping_admission_number"]
    duplicates = admissions.ne("") & admissions.duplicated(keep=False)
    for index in result.index[duplicates]:
        reason = "admission number duplicate"
        if result.at[index, "mapping_status"] == "Review" and result.at[index, "mapping_reason"].startswith(reason):
            continue
        if result.at[index, "mapping_status"] == "Review":
            reason += "; " + result.at[index, "mapping_reason"]
        result.at[index, "mapping_status"] = "Review"
        result.at[index, "mapping_reason"] = reason
    return result


def review_duplicate_usernames(result):
    """Review usernames or user IDs shared by multiple matched records."""
    from .account_duplicates import duplicate_account_positions

    username_rows = {}
    matched = result[result["mapping_status"] == "Matched"]
    for _, row in matched.iterrows():
        username = str(row["mapping_username"]).strip()
        if username:
            username_rows.setdefault(username, []).append(row["mapping_dump_row"])

    positions = duplicate_account_positions(
        ["Matched"] * len(matched), matched["mapping_username"], matched["mapping_user_id"])
    for position in sorted(positions):
        index = matched.index[position]
        value = matched.at[index, "mapping_username"]
        username = str(value).strip()
        rows = username_rows.get(username, [])
        if len(rows) > 1:
            reason = f"duplicate username found; dump rows: {', '.join(map(str, rows))}"
        else:
            user_id = str(matched.at[index, "mapping_user_id"]).strip()
            id_rows = matched.loc[matched["mapping_user_id"].astype(str).str.strip().eq(user_id), "mapping_dump_row"]
            reason = f"duplicate user ID found; dump rows: {', '.join(map(str, id_rows))}"
        result.at[index, "mapping_status"] = "Review"
        result.at[index, "mapping_reason"] = reason
    return result
