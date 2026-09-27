"""Persistent bulk-registration manifests and file snapshots with inactivity expiry."""
from functools import wraps
import hashlib
import json
from pathlib import Path
import shutil
from threading import RLock
import time
from uuid import UUID, uuid4

from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[2] / 'storage' / 'bulk_registration'
LOCK = RLock()
WORKSPACE_TTL_SECONDS = 24 * 60 * 60


def workspace_locked(operation):
    """Serialize complete operations in the supported single-worker server.

    Readers must also hold the lock while using snapshot references: a writer
    can remove an old snapshot immediately after publishing its replacement.
    """
    @wraps(operation)
    def locked(*args, **kwargs):
        with LOCK:
            return operation(*args, **kwargs)
    return locked


def _folder(workspace_id):
    try:
        workspace_id = str(UUID(str(workspace_id)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(404, 'Bulk registration workspace not found.') from exc
    folder = ROOT / workspace_id
    if folder.resolve().parent != ROOT.resolve():
        raise HTTPException(404, 'Bulk registration workspace not found.')
    return folder


@workspace_locked
def create_workspace():
    cleanup_expired_workspaces()
    workspace_id = str(uuid4())
    save_workspace(workspace_id, {
        'workspace_id': workspace_id, 'revision': 0, 'path': '', 'file': None,
        'school_index': '', 'school': None, 'output': None, 'outputs': {},
    })
    return workspace_id


def _is_expired(folder, now=None):
    manifest = folder / 'state.json'
    try:
        last_activity = manifest.stat().st_mtime
    except OSError:
        return False
    return (time.time() if now is None else now) - last_activity >= WORKSPACE_TTL_SECONDS


@workspace_locked
def cleanup_expired_workspaces(now=None):
    """Delete bulk workspaces inactive for at least 24 hours."""
    if not ROOT.is_dir():
        return 0
    removed = 0
    for folder in ROOT.iterdir():
        try:
            valid = (folder.is_dir() and not folder.is_symlink()
                     and str(UUID(folder.name)) == folder.name
                     and folder.resolve().parent == ROOT.resolve())
        except (ValueError, OSError):
            valid = False
        if valid and _is_expired(folder, now):
            shutil.rmtree(folder)
            removed += 1
    return removed


@workspace_locked
def load_workspace(workspace_id, touch=True):
    folder = _folder(workspace_id)
    manifest = folder / 'state.json'
    if not manifest.is_file():
        raise HTTPException(404, 'Bulk registration workspace not found.')
    if _is_expired(folder):
        shutil.rmtree(folder)
        raise HTTPException(404, 'Bulk registration workspace expired.')
    try:
        state = json.loads(manifest.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HTTPException(409, 'Bulk registration workspace metadata is unreadable.') from exc
    if touch:
        manifest.touch()
    return state


@workspace_locked
def read_snapshot(workspace_id, reference):
    folder = _folder(workspace_id)
    if not isinstance(reference, dict) or not isinstance(reference.get('file'), str):
        raise HTTPException(409, 'Saved bulk registration file reference is invalid.')
    target = (folder / reference['file']).resolve()
    if target.parent != folder.resolve() or not target.is_file():
        raise HTTPException(409, 'Saved bulk registration file is missing.')
    return reference.get('metadata', {}), target.read_bytes()


def save_workspace(workspace_id, state, snapshots=None):
    """Atomically publish a manifest after writing all supplied snapshot bytes."""
    snapshots = snapshots or {}
    folder = _folder(workspace_id)
    with LOCK:
        folder.mkdir(parents=True, exist_ok=True)
        for key, (metadata, data) in snapshots.items():
            filename = hashlib.sha256(data).hexdigest() + '.bin'
            target = folder / filename
            if not target.exists():
                pending = folder / f'{filename}.pending'
                try:
                    pending.write_bytes(data)
                    pending.replace(target)
                finally:
                    pending.unlink(missing_ok=True)
            reference = {'metadata': metadata, 'file': filename}
            if key.startswith('_output_'):
                state.setdefault('outputs', {})[key.removeprefix('_output_')] = reference
            else:
                state[key] = reference
        pending_manifest = folder / 'state.pending.json'
        pending_manifest.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
        pending_manifest.replace(folder / 'state.json')
        referenced = set()
        for key in ('input',):
            if isinstance(state.get(key), dict) and isinstance(state[key].get('file'), str):
                referenced.add(state[key]['file'])
        for reference in state.get('outputs', {}).values():
            if isinstance(reference, dict) and isinstance(reference.get('file'), str):
                referenced.add(reference['file'])
        for target in folder.glob('*.bin'):
            if target.name not in referenced:
                target.unlink(missing_ok=True)
        return state


@workspace_locked
def save_input(workspace_id, metadata, data):
    state = load_workspace(workspace_id)
    state['outputs'] = {}
    state['revision'] = int(state.get('revision', 0)) + 1
    return save_workspace(workspace_id, state, {'input': (metadata, data)})


@workspace_locked
def save_output(workspace_id, key, metadata, data):
    state = load_workspace(workspace_id)
    state['revision'] = int(state.get('revision', 0)) + 1
    return save_workspace(workspace_id, state, {f'_output_{key}': (metadata, data)})


@workspace_locked
def update_input_metadata(workspace_id, metadata):
    state = load_workspace(workspace_id)
    if not isinstance(state.get('input'), dict):
        raise HTTPException(409, 'Saved bulk registration input is missing.')
    state['input']['metadata'] = metadata
    state['revision'] = int(state.get('revision', 0)) + 1
    return save_workspace(workspace_id, state)


def delete_workspace(workspace_id):
    folder = _folder(workspace_id)
    with LOCK:
        if folder.is_dir() and not folder.is_symlink():
            shutil.rmtree(folder)
