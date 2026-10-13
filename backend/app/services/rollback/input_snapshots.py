"""Uploaded rollback input snapshot persistence."""

import hashlib

from fastapi import HTTPException

from app.services.rollback import config
from app.services.rollback.workspace import folder_for, load_state, save_state


def save_input(workspace_id, metadata, data):
    folder = folder_for(workspace_id)
    filename = hashlib.sha256(data).hexdigest() + '.bin'
    with config.LOCK:
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
            if not snapshot.name.startswith('dump-') and snapshot.name != filename:
                snapshot.unlink(missing_ok=True)
        return state


def update_input_metadata(workspace_id, metadata):
    with config.LOCK:
        state = load_state(workspace_id)
        if not isinstance(state.get('input'), dict):
            raise HTTPException(409, 'Upload a rollback file first.')
        state['input']['metadata'] = metadata
        save_state(workspace_id, state)
        return state


def clear_input(workspace_id):
    folder = folder_for(workspace_id)
    with config.LOCK:
        state = load_state(workspace_id)
        reference = state.get('input')
        state['input'] = None
        save_state(workspace_id, state)
        if isinstance(reference, dict) and isinstance(reference.get('file'), str):
            target = (folder / reference['file']).resolve()
            if target.parent == folder.resolve() and not target.name.startswith('dump-'):
                target.unlink(missing_ok=True)
        return state


def read_input(workspace_id):
    with config.LOCK:
        state = load_state(workspace_id)
        reference = state.get('input')
        if not isinstance(reference, dict) or not isinstance(reference.get('file'), str):
            raise HTTPException(409, 'Upload a rollback file first.')
        folder = folder_for(workspace_id)
        target = (folder / reference['file']).resolve()
        if target.parent != folder.resolve() or not target.is_file():
            raise HTTPException(409, 'Saved rollback file is missing.')
        return reference.get('metadata', {}), target.read_bytes()
