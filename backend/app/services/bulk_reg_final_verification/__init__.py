"""Public API for modular final bulk-registration verification."""

from .repair import repair_conflicting_usernames
from .runner import verify_final_output

__all__ = ['repair_conflicting_usernames', 'verify_final_output']
