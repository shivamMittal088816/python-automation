"""Build matched, review, and unmatched email workbooks."""
from Backend.services.admission_mapping.admission_workbook import build_workbook


def build_email_exports(school, records):
    result = school.copy()
    for column in ("email_mapping_email", "email_mapping_dump_full_name", "email_mapping_status",
                   "email_mapping_user_id", "email_mapping_username"):
        result[column] = [record[column] for record in records]
    groups = [record["_email_group"] for record in records]
    return {f"email_{name}.xlsx": build_workbook(result.loc[
                [group == status for group in groups]], status)
            for status, name in (("Matched", "matched"), ("Review", "review"), ("Not Matched", "not_matched"))}
