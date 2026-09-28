"""Build matched, review, and unmatched class and full name workbooks."""
from app.services.admission_mapping.admission_workbook import build_workbook


def build_full_name_class_exports(rows, groups):
    return {f"full_name_class_{filename}.xlsx": build_workbook(
                rows.loc[[group == status for group in groups]], status)
            for status, filename in (("Matched", "matched"), ("Review", "review"),
                                     ("Not Matched", "not_matched"))}

# Purpose: Build matched, review, and unmatched class and full name workbooks.
# Its public interface includes build_full_name_class_exports.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.full_name_class_mapping.full_name_class_mapping_pipeline.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
