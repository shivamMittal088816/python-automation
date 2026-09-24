"""Move conflicting account assignments across mapping stages into Review."""

from io import BytesIO

import pandas as pd

from Backend.services.admission_mapping.account_duplicates import duplicate_account_positions
from Backend.services.admission_mapping.admission_workbook import build_workbook


STAGES = (
    ("admission_exports", "", "mapping"),
    ("email_exports", "email_", "email_mapping"),
    ("full_name_class_exports", "full_name_class_", "full_name_class"),
)


def review_duplicate_accounts(state):
    """Check both identifiers across stages; preserve duplicate Review reservations.

    All conflicting Matched rows move, including earlier-stage matches. Rows
    already reviewed for duplicate accounts keep reserving those identifiers
    so rerunning another stage cannot silently accept the same account again.
    """
    tables = {}
    references, usernames, user_ids = [], [], []
    for state_key, filename_prefix, column_prefix in STAGES:
        exports = state.get(state_key, {})
        for group in ("matched", "review"):
            filename = f"{filename_prefix}{group}.xlsx"
            snapshot = exports.get(filename)
            if not snapshot or not snapshot["count"]:
                continue
            rows = pd.read_excel(BytesIO(snapshot["data"]), dtype=str, keep_default_na=False)
            tables[(state_key, group)] = rows
            for position, row in rows.iterrows():
                status = str(row.get(f"{column_prefix}_status", ""))
                reason = status + " " + str(row.get("mapping_reason", ""))
                duplicate_review = any(marker in reason.lower() for marker in
                                       ("duplicate username", "duplicate user id"))
                if group == "review" and not duplicate_review:
                    continue
                references.append((state_key, group, position))
                usernames.append(row.get(f"{column_prefix}_username", ""))
                user_ids.append(row.get(f"{column_prefix}_user_id", ""))

    conflicts = duplicate_account_positions(["Matched"] * len(references), usernames, user_ids)
    moves = {}
    for position in conflicts:
        state_key, group, row_position = references[position]
        if group == "matched":
            moves.setdefault(state_key, set()).add(row_position)

    replacements = {}
    for state_key, filename_prefix, column_prefix in STAGES:
        positions = moves.get(state_key)
        if not positions:
            continue
        matched = tables[(state_key, "matched")]
        moved = matched.loc[sorted(positions)].copy()
        reason = "Duplicate username or user ID across mapping results"
        status_column = f"{column_prefix}_status"
        if column_prefix == "mapping" and "mapping_reason" in moved.columns:
            moved["mapping_reason"] = moved["mapping_reason"].map(lambda old: reason + "; " + old)
            moved[status_column] = "Review"
        else:
            moved[status_column] = moved[status_column].map(lambda old: f"Review — {reason}; previous: {old}")
        previous = tables.get((state_key, "review"))
        if previous is not None:
            moved = pd.concat([previous, moved], ignore_index=True)
        exports = dict(state[state_key])
        exports[f"{filename_prefix}matched.xlsx"] = build_workbook(matched.drop(index=sorted(positions)), "Matched")
        exports[f"{filename_prefix}review.xlsx"] = build_workbook(moved, "Review")
        replacements[state_key] = exports

    # Publish only after every replacement workbook has been built successfully.
    if replacements:
        from Backend.utils.file_snapshots import store_exports
        stored = {key: store_exports(exports) for key, exports in replacements.items()}
        state.update(stored)
    return sum(map(len, moves.values()))
