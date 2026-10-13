"""Rollback workspace identity, expiry, and manifest persistence."""

import json
import shutil
import time
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.services.rollback import config


def folder_for(workspace_id):
    try:
        workspace_id = str(UUID(str(workspace_id)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(404, 'Rollback workspace not found.') from exc
    folder = config.ROOT / workspace_id
    if folder.resolve().parent != config.ROOT.resolve():
        raise HTTPException(404, 'Rollback workspace not found.')
    return folder


def _expired(folder, now=None):
    manifest = folder / 'state.json'
    try:
        last_activity = manifest.stat().st_mtime
    except OSError:
        return False
    return (time.time() if now is None else now) - last_activity >= config.WORKSPACE_TTL_SECONDS


def cleanup_expired_workspaces(now=None):
    if not config.ROOT.is_dir():
        return
    for folder in config.ROOT.iterdir():
        try:
            valid = (folder.is_dir() and not folder.is_symlink()
                     and str(UUID(folder.name)) == folder.name
                     and folder.resolve().parent == config.ROOT.resolve())
        except (ValueError, OSError):
            valid = False
        if valid and _expired(folder, now):
            shutil.rmtree(folder)


def create_workspace():
    with config.LOCK:
        cleanup_expired_workspaces()
        workspace_id = str(uuid4())
        save_state(workspace_id, {
            'workspace_id': workspace_id, 'school': None, 'input': None, 'dump': None,
        })
        return workspace_id


def load_state(workspace_id, touch=True):
    folder = folder_for(workspace_id)
    manifest = folder / 'state.json'
    with config.LOCK:
        if not manifest.is_file() or _expired(folder):
            if folder.is_dir() and _expired(folder):
                shutil.rmtree(folder)
            raise HTTPException(404, 'Rollback workspace not found or expired.')
        try:
            state = json.loads(manifest.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise HTTPException(409, 'Rollback workspace metadata is unreadable.') from exc
        if touch:
            manifest.touch()
        return state


def save_state(workspace_id, state):
    folder = folder_for(workspace_id)
    with config.LOCK:
        folder.mkdir(parents=True, exist_ok=True)
        pending = folder / 'state.pending.json'
        pending.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
        pending.replace(folder / 'state.json')
