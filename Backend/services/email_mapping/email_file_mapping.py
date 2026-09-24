"""Public imports for the reusable email mapping implementation."""
from .email_input import email_input_signature, email_school_input, sync_email_stage
from .email_mapping_pipeline import map_by_email

__all__ = ["email_input_signature", "email_school_input", "sync_email_stage", "map_by_email"]
