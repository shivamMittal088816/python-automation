"""Persistent rollback file snapshots with isolated browser workspaces."""

import hashlib
import csv
from contextlib import contextmanager
from itertools import islice
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
            'workspace_id': workspace_id, 'school': None, 'input': None, 'dump': None,
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
            if not snapshot.name.startswith('dump-') and snapshot.name != filename:
                snapshot.unlink(missing_ok=True)
        return state


def _write_dump_snapshot(folder, columns, rows):
    pending = folder / f'dump-{uuid4()}.pending'
    row_count = 0
    try:
        with pending.open('w', encoding='utf-8', newline='') as target:
            writer = csv.writer(target, lineterminator='\n')
            writer.writerow(columns)
            for row in rows:
                writer.writerow(row)
                row_count += 1
        digest = hashlib.sha256()
        with pending.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
        filename = f'dump-{digest.hexdigest()}.bin'
        target = folder / filename
        if target.exists():
            pending.unlink()
        else:
            pending.replace(target)
        return {
            'file': filename, 'format': 'csv',
            'row_count': row_count, 'columns': list(columns),
        }
    finally:
        pending.unlink(missing_ok=True)


def _delete_dump_snapshot(folder, reference):
    if not isinstance(reference, dict) or not isinstance(reference.get('file'), str):
        return
    target = (folder / reference['file']).resolve()
    if (target.parent == folder.resolve()
            and (target.name.startswith('dump-') or target.name == 'dump.json')):
        target.unlink(missing_ok=True)


def save_school_rows(workspace_id, school, columns, rows):
    with LOCK:
        folder = _folder(workspace_id)
        state = load_state(workspace_id)
        previous = state.get('dump')
        reference = _write_dump_snapshot(folder, columns, rows)
        state['school'] = school
        state['dump'] = reference
        # Commit the new reference before retiring the previous snapshot.
        save_state(workspace_id, state)
        if previous != reference:
            _delete_dump_snapshot(folder, previous)
        for snapshot in folder.glob('dump-*.bin'):
            if snapshot.name != reference['file']:
                snapshot.unlink(missing_ok=True)
        return state


def save_school(workspace_id, school, dump=None):
    """Compatibility wrapper for callers that already hold materialized rows."""
    if dump is None:
        with LOCK:
            state = load_state(workspace_id)
            state['school'] = school
            save_state(workspace_id, state)
            return state
    return save_school_rows(
        workspace_id, school, dump.get('columns', []), dump.get('rows', []),
    )


def clear_school(workspace_id):
    with LOCK:
        state = load_state(workspace_id)
        reference = state.get('dump')
        state['school'] = None
        state['dump'] = None
        save_state(workspace_id, state)
        _delete_dump_snapshot(_folder(workspace_id), reference)
        return state


def _migrate_legacy_dump(workspace_id, state):
    reference = state.get('dump')
    if not isinstance(reference, dict) or reference.get('file') != 'dump.json':
        return state
    folder = _folder(workspace_id)
    legacy = folder / 'dump.json'
    try:
        dump = json.loads(legacy.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HTTPException(409, 'Saved rollback dump is missing or unreadable.') from exc
    if not isinstance(dump, dict) or not isinstance(dump.get('columns'), list) or not isinstance(dump.get('rows'), list):
        raise HTTPException(409, 'Saved rollback dump is unreadable.')
    migrated = _write_dump_snapshot(folder, dump['columns'], dump['rows'])
    state['dump'] = migrated
    save_state(workspace_id, state)
    legacy.unlink(missing_ok=True)
    return state


@contextmanager
def open_dump_rows(workspace_id):
    with LOCK:
        state = load_state(workspace_id)
        state = _migrate_legacy_dump(workspace_id, state)
        reference = state.get('dump')
        if not isinstance(reference, dict) or not isinstance(reference.get('file'), str):
            raise HTTPException(409, 'Verify a school first.')
        folder = _folder(workspace_id)
        target = (folder / reference['file']).resolve()
        if (target.parent != folder.resolve() or not target.name.startswith('dump-')
                or not target.is_file()):
            raise HTTPException(409, 'Saved rollback dump is missing or unreadable.')
        try:
            with target.open('r', encoding='utf-8', newline='') as source:
                reader = csv.reader(source)
                columns = next(reader, [])
                if columns != reference.get('columns'):
                    raise HTTPException(409, 'Saved rollback dump is unreadable.')
                yield columns, reader, int(reference.get('row_count', 0))
        except (OSError, UnicodeError, csv.Error) as exc:
            raise HTTPException(409, 'Saved rollback dump is missing or unreadable.') from exc


def read_dump_page(workspace_id, page, page_size):
    if page < 1:
        raise HTTPException(400, 'The requested dump preview page does not exist.')
    with open_dump_rows(workspace_id) as (columns, rows, row_count):
        total_pages = max(1, (row_count + page_size - 1) // page_size)
        if page > total_pages:
            raise HTTPException(400, 'The requested dump preview page does not exist.')
        start = (page - 1) * page_size
        visible = list(islice(rows, start, start + page_size))
    return {
        'columns': columns, 'rows': visible, 'row_count': row_count,
        'page': page, 'page_size': page_size, 'total_pages': total_pages,
    }


def read_dump(workspace_id):
    """Compatibility helper for tests and small internal callers."""
    with open_dump_rows(workspace_id) as (columns, rows, _):
        return {'columns': columns, 'rows': list(rows)}


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
        reference = state.get('input')
        state['input'] = None
        save_state(workspace_id, state)
        if isinstance(reference, dict) and isinstance(reference.get('file'), str):
            target = (folder / reference['file']).resolve()
            if target.parent == folder.resolve() and not target.name.startswith('dump-'):
                target.unlink(missing_ok=True)
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
