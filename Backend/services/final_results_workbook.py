"""Build one final workbook without merging result schemas across mapping stages."""

from io import BytesIO
from pathlib import Path
import re

import pandas as pd


FINAL_RESULT_SHEETS = (
    ('admission_exports', 'matched.xlsx', 'Admission Matched'),
    ('admission_exports', 'review.xlsx', 'Admission Review'),
    ('admission_exports', 'not_matched.xlsx', 'Admission Not Matched'),
    ('email_exports', 'email_matched.xlsx', 'Email Matched'),
    ('email_exports', 'email_review.xlsx', 'Email Review'),
    ('full_name_class_exports', 'full_name_class_matched.xlsx', 'Class Matched'),
    ('full_name_class_exports', 'full_name_class_review.xlsx', 'Class Review'),
    ('full_name_class_exports', 'full_name_class_not_matched.xlsx', 'Final Not Matched'),
)


def _filename_part(value, fallback):
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(value or '')).strip(' .-')
    return (cleaned or fallback)[:120]


def final_results_filename(state):
    school = state.get('saved_admission_dump', {})
    index = _filename_part(school.get('school_index'), 'school-index')
    fallback_name = Path(state.get('saved_admission_school', {}).get('name', '')).stem
    name = _filename_part(school.get('school_name'), fallback_name or 'school-name')
    return f'automation-{index}-{name}.xlsx'


def final_results_available(state):
    return any(state.get(stage, {}).get(filename) for stage, filename, _ in FINAL_RESULT_SHEETS)


def build_final_results_workbook(state):
    """Return an XLSX containing each final result group in an independent sheet."""
    if not final_results_available(state):
        raise ValueError('Run at least one mapping before downloading mapping results.')

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for stage, filename, sheet_name in FINAL_RESULT_SHEETS:
            snapshot = state.get(stage, {}).get(filename)
            if not snapshot:
                continue
            rows = pd.read_excel(BytesIO(snapshot['data']), dtype=str, keep_default_na=False)
            rows.to_excel(writer, sheet_name=sheet_name, index=False)
            # Uploaded values that resemble formulas must remain literal text.
            for cells in writer.sheets[sheet_name].iter_rows():
                for cell in cells:
                    if cell.data_type == 'f':
                        cell.data_type = 's'
    return output.getvalue()
