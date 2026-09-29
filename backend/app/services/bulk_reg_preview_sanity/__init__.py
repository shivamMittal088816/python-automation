"""Field-level sanity checks used by the generated bulk-registration preview."""

from .class_number import missing_class_records
from .email import duplicate_email_records, invalid_email_records
from .first_name import invalid_first_name_records
from .full_name import blank_full_name_records
from .gender import missing_gender_records
from .review import build_review_records
from .section import apply_section_ids

__all__ = [
    'apply_section_ids',
    'blank_full_name_records',
    'build_review_records',
    'duplicate_email_records',
    'invalid_email_records',
    'invalid_first_name_records',
    'missing_class_records',
    'missing_gender_records',
]
