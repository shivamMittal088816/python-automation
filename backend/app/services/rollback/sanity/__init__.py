"""Public entry point for rollback-file sanity validation."""

from app.services.rollback.sanity.checker import check_rollback_input

__all__ = ['check_rollback_input']
