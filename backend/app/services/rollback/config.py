"""Shared rollback workspace configuration and synchronization."""

from pathlib import Path
from threading import RLock


ROOT = Path(__file__).resolve().parents[3] / 'storage' / 'rollback'
LOCK = RLock()
WORKSPACE_TTL_SECONDS = 24 * 60 * 60
