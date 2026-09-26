"""Session creation, inactivity expiry and locked workflow access."""
from contextlib import contextmanager
from pathlib import Path
import shutil
from threading import RLock
import time
from uuid import UUID, uuid4

from fastapi import HTTPException
from app.api.file_workflow_session_storage import (
    EXPORT_KEYS, FILE_KEYS, load_state, save_state,
)
from app.services.email_mapping.email_file_mapping import sync_email_stage

ROOT = Path(__file__).resolve().parents[2] / 'storage' / 'temp' / 'workflow_sessions'
SESSION_TTL_SECONDS = 24 * 60 * 60
LOCK = RLock()


def session_folder(session_id):
    try:
        if str(UUID(session_id)) != session_id:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(404, 'Mapping session not found.')
    return ROOT / session_id


def _session_directory(folder):
    """Accept only canonical UUID folders directly inside the session root."""
    try:
        return (not folder.is_symlink()
                and str(UUID(folder.name)) == folder.name
                and folder.resolve().parent == ROOT.resolve())
    except (ValueError, TypeError, AttributeError, OSError):
        return False


def _last_activity(folder):
    manifest = folder / 'state.json'
    target = manifest if manifest.is_file() else folder
    try:
        return target.stat().st_mtime
    except OSError:
        return None


def _is_expired(folder, now=None):
    last_activity = _last_activity(folder)
    return last_activity is not None and (time.time() if now is None else now) - last_activity >= SESSION_TTL_SECONDS


def _remove_session(folder):
    if _session_directory(folder) and folder.is_dir():
        shutil.rmtree(folder)


def cleanup_expired_sessions(now=None):
    """Remove UUID session folders inactive for at least 24 hours."""
    if not ROOT.is_dir():
        return 0
    current_time = time.time() if now is None else now
    removed = 0
    for folder in ROOT.iterdir():
        if _session_directory(folder) and folder.is_dir() and _is_expired(folder, current_time):
            _remove_session(folder)
            removed += 1
    return removed


def create_session(school_index=None):
    """Start an empty workspace, retaining an optional school index."""
    with LOCK:
        cleanup_expired_sessions()
        session_id = str(uuid4())
        state = {
            'workspace_id': str(uuid4()),
            'revision': 0,
            'admission_settings': {
                'workspace_school_index': str(school_index).strip() if school_index else '',
            },
        }
        save_state(session_folder(session_id), state)
        return session_id


@contextmanager
def workspace(session_id, persist=True, expected_revision=None):
    # Serialize operations within the existing single-worker development app.
    with LOCK:
        folder = session_folder(session_id)
        if _session_directory(folder) and folder.is_dir() and _is_expired(folder):
            _remove_session(folder)
            raise HTTPException(404, 'Mapping session expired. A new session will be created.')
        state = load_state(folder)
        current_revision = int(state.get('revision', 0))
        if expected_revision is not None and expected_revision != current_revision:
            raise HTTPException(
                409,
                'This workspace changed in another tab or request. Reload it and try again.',
            )
        # Reading a valid session counts as activity, including read-only previews.
        (folder / 'state.json').touch()
        if persist:
            state['revision'] = current_revision + 1
        try:
            yield state
        except Exception:
            raise
        else:
            if persist:
                sync_email_stage(state)
                save_state(folder, state)
