"""Classify admissions by missing values, dump occurrences and first names."""

import pandas as pd

from .admission_name_comparison import school_first_name

def classify_school_rows(school, school_admission_column, name_column, name_is_full, lookup, counts, occurrence_rows):
    admissions = school[school_admission_column].fillna("").astype(str).str.strip()
    duplicate_admissions = set(admissions[admissions.ne("") & admissions.duplicated(keep=False)])
    records = []
    for _, row in school.iterrows():
        value = row[school_admission_column]
        admission = str(value).strip() if pd.notna(value) else ""
        if not admission:
            records.append({
                "mapping_admission_number": admission,
                "mapping_username": "",
                "mapping_user_id": "",
                "mapping_first_name": "",
                "mapping_dump_first_name": "",
                "mapping_dump_row": "",
                "mapping_dump_count": counts.get(admission, 0),
                "mapping_status": "Not Matched",
                "mapping_reason": "Admission number missing",
            })
            continue
        first_name = school_first_name(row[name_column], name_is_full)
        if admission in duplicate_admissions:
            reason = "admission number duplicate"
            if not first_name:
                reason += "; School firstName missing"
            records.append({
                "mapping_admission_number": admission,
                "mapping_username": "",
                "mapping_user_id": "",
                "mapping_first_name": first_name,
                "mapping_dump_first_name": "",
                "mapping_dump_row": "",
                "mapping_dump_count": counts.get(admission, 0),
                "mapping_status": "Review",
                "mapping_reason": reason,
            })
            continue
        dump_first_name = ""
        if counts.get(admission, 0) == 1 and admission in lookup:
            dump_first_name = school_first_name(lookup[admission][2], False)
        if not first_name:
            dump_rows = ", ".join(str(number) for number in occurrence_rows.get(admission, []))
            reason = "School firstName missing"
            if counts.get(admission, 0) > 1:
                reason += f"; more than one occurrence; dump rows: {dump_rows}"
            elif dump_rows:
                reason += f"; dump row: {dump_rows}"
            records.append({
                "mapping_admission_number": admission,
                "mapping_username": "",
                "mapping_user_id": "",
                "mapping_first_name": "",
                "mapping_dump_first_name": dump_first_name,
                "mapping_dump_row": dump_rows,
                "mapping_dump_count": counts.get(admission, 0),
                "mapping_status": "Review",
                "mapping_reason": reason,
            })
            continue
        if counts.get(admission, 0) > 1:
            dump_rows = ", ".join(str(number) for number in occurrence_rows[admission])
            records.append({
                "mapping_admission_number": admission,
                "mapping_username": "",
                "mapping_user_id": "",
                "mapping_first_name": "",
                "mapping_dump_first_name": "",
                "mapping_dump_row": dump_rows,
                "mapping_dump_count": counts[admission],
                "mapping_status": "Review",
                "mapping_reason": f"more than one occurrence; dump rows: {dump_rows}",
            })
            continue
        username, dump_row, dump_name, user_id = lookup.get(admission, ("", "", "", ""))

        # An admission miss is Not Matched; an admission hit with a name problem needs Review.
        if admission not in lookup:
            reason = "Admission number not found"
        elif not dump_first_name:
            reason = f"Dump first name missing; dump row: {dump_row}"
        elif dump_first_name != first_name:
            reason = f"First name does not match between school and dump; dump row: {dump_row}"
        elif len(first_name.replace(".", "").strip()) == 1:
            reason = f"First name matches but is only 1 character; dump row: {dump_row}"
        elif not username:
            reason = f"Username missing; dump row: {dump_row}"
        else:
            reason = "Admission number and first name match"

        matched = reason == "Admission number and first name match"
        records.append({
            "mapping_admission_number": admission,
            "mapping_username": username,
            "mapping_user_id": str(user_id).strip() if matched and pd.notna(user_id) else "",
            "mapping_first_name": first_name,
            "mapping_dump_first_name": dump_first_name,
            "mapping_dump_row": dump_row,
            "mapping_dump_count": counts.get(admission, 0),
            "mapping_status": (
                "Not Matched" if admission not in lookup
                else "Matched" if matched else "Review"
            ),
            "mapping_reason": reason,
        })
    return records
