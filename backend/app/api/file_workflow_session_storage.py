"""Serialize and restore session manifests and content-addressed file snapshots."""
import hashlib
import json
from fastapi import HTTPException
from app.utils.file_snapshots import StoredFile


FILE_KEYS = ('saved_admission_school', 'saved_admission_dump', 'saved_email_dump')
EXPORT_KEYS = ('admission_exports', 'email_exports', 'full_name_class_exports')


def save_state(folder, state):
    """Publish the manifest only after each referenced snapshot is on disk."""
    folder.mkdir(parents=True, exist_ok=True)
    manifest = dict(state)
    def snapshot(item):
        data = item['data']
        filename = hashlib.sha256(data).hexdigest() + '.bin'
        target = folder / filename
        if not target.exists():
            staged_snapshot = folder / f'{filename}.pending'
            try:
                staged_snapshot.write_bytes(data)
                staged_snapshot.replace(target)
            finally:
                staged_snapshot.unlink(missing_ok=True)
        return {'metadata': {key: item[key] for key in item if key != 'data'}, 'file': filename}
    for key in FILE_KEYS:
        if manifest.get(key) is not None:
            manifest[key] = snapshot(manifest[key])
    for key in EXPORT_KEYS:
        if key in manifest:
            manifest[key] = {name: snapshot(item) for name, item in manifest[key].items()}
    staged = folder / 'state.pending.json'
    staged.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
    staged.replace(folder / 'state.json')
    referenced = {
        item['file']
        for key in FILE_KEYS
        if isinstance((item := manifest.get(key)), dict) and isinstance(item.get('file'), str)
    }
    for key in EXPORT_KEYS:
        referenced.update(
            item['file'] for item in manifest.get(key, {}).values()
            if isinstance(item, dict) and isinstance(item.get('file'), str)
        )
    for target in folder.glob('*.bin'):
        if target.name not in referenced and target.is_file() and not target.is_symlink():
            target.unlink(missing_ok=True)
    for target in folder.glob('*.pending'):
        if target.is_file() and not target.is_symlink():
            target.unlink(missing_ok=True)


def load_state(folder):
    manifest = folder / 'state.json'
    if not manifest.is_file():
        raise HTTPException(404, 'Mapping session not found.')
    try:
        state = json.loads(manifest.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HTTPException(409, 'Saved mapping session metadata is unreadable. Start a new session.') from exc
    if not isinstance(state, dict):
        raise HTTPException(409, 'Saved mapping session metadata is invalid. Start a new session.')
    # Older manifests predate optimistic concurrency. Keep reads side-effect free
    # while giving those sessions a stable identity and revision until their next
    # successful mutation persists the migrated fields.
    state.setdefault('workspace_id', folder.name)
    state.setdefault('revision', 0)
    def snapshot(item):
        if not isinstance(item, dict) or not isinstance(item.get('file'), str) or not isinstance(item.get('metadata'), dict):
            raise HTTPException(409, 'Saved mapping file reference is invalid. Start a new session.')
        target = (folder / item['file']).resolve()
        if target.parent != folder.resolve() or not target.is_file():
            raise HTTPException(409, 'Saved mapping file is missing or invalid.')
        return StoredFile(target, item['metadata'])
    for key in FILE_KEYS:
        if state.get(key) is not None:
            state[key] = snapshot(state[key])
    for key in EXPORT_KEYS:
        if key in state:
            state[key] = {name: snapshot(item) for name, item in state[key].items()}
    if state.get('admission_signature'):
        state['admission_signature'] = tuple(state['admission_signature'])
    return state
