"""Database dump snapshots, migration, paging, and school state."""

import csv
from contextlib import contextmanager
import hashlib
from itertools import islice
import json
from uuid import uuid4

from fastapi import HTTPException

from app.services.rollback import config
from app.services.rollback.workspace import folder_for, load_state, save_state


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
    with config.LOCK:
        folder = folder_for(workspace_id)
        state = load_state(workspace_id)
        previous = state.get('dump')
        reference = _write_dump_snapshot(folder, columns, rows)
        state['school'] = school
        state['dump'] = reference
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
        with config.LOCK:
            state = load_state(workspace_id)
            state['school'] = school
            save_state(workspace_id, state)
            return state
    return save_school_rows(
        workspace_id, school, dump.get('columns', []), dump.get('rows', []),
    )


def clear_school(workspace_id):
    with config.LOCK:
        state = load_state(workspace_id)
        reference = state.get('dump')
        state['school'] = None
        state['dump'] = None
        save_state(workspace_id, state)
        _delete_dump_snapshot(folder_for(workspace_id), reference)
        return state


def _migrate_legacy_dump(workspace_id, state):
    reference = state.get('dump')
    if not isinstance(reference, dict) or reference.get('file') != 'dump.json':
        return state
    folder = folder_for(workspace_id)
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
    with config.LOCK:
        state = _migrate_legacy_dump(workspace_id, load_state(workspace_id))
        reference = state.get('dump')
        if not isinstance(reference, dict) or not isinstance(reference.get('file'), str):
            raise HTTPException(409, 'Verify a school first.')
        folder = folder_for(workspace_id)
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
