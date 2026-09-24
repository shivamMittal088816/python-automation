"""Build matched, review, and unmatched class and full name workbooks."""
from Backend.services.admission_mapping.admission_workbook import build_workbook


def build_full_name_class_exports(rows, groups):
    return {f"full_name_class_{filename}.xlsx": build_workbook(
                rows.loc[[group == status for group in groups]], status)
            for status, filename in (("Matched", "matched"), ("Review", "review"),
                                     ("Not Matched", "not_matched"))}
