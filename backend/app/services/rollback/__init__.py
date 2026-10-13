"""Public API for modular rollback workspace persistence."""

from app.services.rollback import config
from app.services.rollback.dump_snapshots import (
    clear_school, open_dump_rows, read_dump, read_dump_page,
    save_school, save_school_rows,
)
from app.services.rollback.input_snapshots import (
    clear_input, read_input, save_input, update_input_metadata,
)
from app.services.rollback.workspace import (
    cleanup_expired_workspaces, create_workspace, load_state, save_state,
)


def root_path():
    return config.ROOT


__all__ = [
    'cleanup_expired_workspaces', 'clear_input', 'clear_school', 'config',
    'create_workspace', 'load_state', 'open_dump_rows', 'read_dump',
    'read_dump_page', 'read_input', 'root_path', 'save_input', 'save_school',
    'save_school_rows', 'save_state', 'update_input_metadata',
]
