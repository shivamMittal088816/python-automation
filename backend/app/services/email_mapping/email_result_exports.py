"""Build matched, review, and unmatched email workbooks."""
from app.services.admission_mapping.admission_input_validation import RESULT_COLUMNS
from app.services.admission_mapping.admission_workbook import build_workbook


def build_email_exports(school, records):
    # An admission result can be used as the input to this stage.  Keep the
    # original school columns, but do not carry the previous stage's audit
    # fields into email exports; they are stale evidence for a different
    # mapping decision and can otherwise be mistaken for email results.
    result = school.drop(columns=RESULT_COLUMNS, errors="ignore").copy()
    for column in ("email_mapping_email", "email_mapping_dump_full_name", "email_mapping_status",
                   "email_mapping_user_id", "email_mapping_username"):
        result[column] = [record[column] for record in records]
    groups = [record["_email_group"] for record in records]
    return {f"email_{name}.xlsx": build_workbook(result.loc[
                [group == status for group in groups]], status)
            for status, name in (("Matched", "matched"), ("Review", "review"), ("Not Matched", "not_matched"))}

# Purpose: Build matched, review, and unmatched email workbooks.
# Its public interface includes build_email_exports.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.email_mapping.email_mapping_pipeline.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
