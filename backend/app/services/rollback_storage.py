"""Persistent rollback file snapshots with isolated browser workspaces."""

import hashlib
import json
from pathlib import Path
import shutil
from threading import RLock
import time
from uuid import UUID, uuid4

from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[2] / 'storage' / 'rollback'
LOCK = RLock()
WORKSPACE_TTL_SECONDS = 24 * 60 * 60


def _folder(workspace_id):
    try:
        workspace_id = str(UUID(str(workspace_id)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(404, 'Rollback workspace not found.') from exc
    folder = ROOT / workspace_id
    if folder.resolve().parent != ROOT.resolve():
        raise HTTPException(404, 'Rollback workspace not found.')
    return folder


def _expired(folder, now=None):
    manifest = folder / 'state.json'
    try:
        last_activity = manifest.stat().st_mtime
    except OSError:
        return False
    return (time.time() if now is None else now) - last_activity >= WORKSPACE_TTL_SECONDS


def cleanup_expired_workspaces(now=None):
    if not ROOT.is_dir():
        return
    for folder in ROOT.iterdir():
        try:
            valid = (folder.is_dir() and not folder.is_symlink()
                     and str(UUID(folder.name)) == folder.name
                     and folder.resolve().parent == ROOT.resolve())
        except (ValueError, OSError):
            valid = False
        if valid and _expired(folder, now):
            shutil.rmtree(folder)


def create_workspace():
    with LOCK:
        cleanup_expired_workspaces()
        workspace_id = str(uuid4())
        save_state(workspace_id, {
            'workspace_id': workspace_id, 'school': None, 'input': None,
        })
        return workspace_id


def load_state(workspace_id, touch=True):
    folder = _folder(workspace_id)
    manifest = folder / 'state.json'
    with LOCK:
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
    folder = _folder(workspace_id)
    with LOCK:
        folder.mkdir(parents=True, exist_ok=True)
        pending = folder / 'state.pending.json'
        pending.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
        pending.replace(folder / 'state.json')


def save_input(workspace_id, metadata, data):
    folder = _folder(workspace_id)
    filename = hashlib.sha256(data).hexdigest() + '.bin'
    with LOCK:
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / filename
        if not target.exists():
            pending = folder / f'{filename}.pending'
            try:
                pending.write_bytes(data)
                pending.replace(target)
            finally:
                pending.unlink(missing_ok=True)
        state = load_state(workspace_id)
        state['input'] = {'file': filename, 'metadata': metadata}
        save_state(workspace_id, state)
        for snapshot in folder.glob('*.bin'):
            if snapshot.name != filename:
                snapshot.unlink(missing_ok=True)
        return state


def save_school(workspace_id, school):
    with LOCK:
        state = load_state(workspace_id)
        state['school'] = school
        save_state(workspace_id, state)
        return state


def clear_school(workspace_id):
    with LOCK:
        state = load_state(workspace_id)
        state['school'] = None
        save_state(workspace_id, state)
        return state


def update_input_metadata(workspace_id, metadata):
    with LOCK:
        state = load_state(workspace_id)
        if not isinstance(state.get('input'), dict):
            raise HTTPException(409, 'Upload a rollback file first.')
        state['input']['metadata'] = metadata
        save_state(workspace_id, state)
        return state


def clear_input(workspace_id):
    folder = _folder(workspace_id)
    with LOCK:
        state = load_state(workspace_id)
        state['input'] = None
        save_state(workspace_id, state)
        for snapshot in folder.glob('*.bin'):
            snapshot.unlink(missing_ok=True)
        return state


def read_input(workspace_id):
    with LOCK:
        state = load_state(workspace_id)
        reference = state.get('input')
        if not isinstance(reference, dict) or not isinstance(reference.get('file'), str):
            raise HTTPException(409, 'Upload a rollback file first.')
        folder = _folder(workspace_id)
        target = (folder / reference['file']).resolve()
        if target.parent != folder.resolve() or not target.is_file():
            raise HTTPException(409, 'Saved rollback file is missing.')
        return reference.get('metadata', {}), target.read_bytes()
