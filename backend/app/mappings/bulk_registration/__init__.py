"""Bulk-registration output schema and value mappings."""

from app.mappings.bulk_registration.class_name import class_id
from app.mappings.bulk_registration.fixed_values import FIXED_VALUES
from app.mappings.bulk_registration.gender import gender_number
from app.mappings.bulk_registration.output_schema import OUTPUT_HEADERS

__all__ = ['FIXED_VALUES', 'OUTPUT_HEADERS', 'class_id', 'gender_number']
