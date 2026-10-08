"""Append-only, workspace-scoped operation audit events."""

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from threading import RLock
from time import perf_counter
from uuid import uuid4
from uuid import UUID


LOG_PATH = Path(__file__).resolve().parents[3] / 'logs' / 'operations.jsonl'
MAX_BYTES = 10 * 1024 * 1024
LOCK = RLock()


OPERATION_ROUTES = {
    ('POST', '/mapping/admission-mapping/run'): ('admission_mapping', 'Admission mapping'),
    ('POST', '/mapping/email-mapping/run'): ('email_mapping', 'Email mapping'),
    ('POST', '/mapping/full-name-class-mapping/run'): ('full_name_class_mapping', 'Full-name and class mapping'),
    ('POST', '/mapping/student-dump/fetch'): ('dump_fetch', 'Student dump fetch'),
    ('POST', '/bulk-reg/files'): ('bulk_file_upload', 'Bulk file upload'),
    ('POST', '/bulk-reg/files/path'): ('bulk_file_load', 'Bulk file load'),
    ('POST', '/bulk-reg/convert'): ('bulk_conversion', 'Bulk registration conversion'),
    ('POST', '/bulk-reg/output/verify'): ('bulk_verification', 'Bulk registration verification'),
}


def _now():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def workspace_reference(value):
    """Keep raw cookie/session tokens out of logs and API responses."""
    return sha256(str(value).encode()).hexdigest() if value else None


def operation_scope(scope, workspace):
    """Return a browser-storage key that identifies both workflow and workspace."""
    reference = workspace_reference(workspace)
    return f'{scope}:{reference}' if scope and reference else None


def valid_client_operation_id(value):
    """Return a canonical UUID supplied by the browser, or ``None``."""
    try:
        parsed = UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None
    return str(parsed) if parsed.version == 4 else None


def _rotate():
    if not LOG_PATH.is_file() or LOG_PATH.stat().st_size < MAX_BYTES:
        return
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    LOG_PATH.replace(LOG_PATH.with_name(f'operations-{stamp}.jsonl'))


def _append(event):
    with LOCK:
        try:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            _rotate()
            with LOG_PATH.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n')
        except OSError:
            # Audit logging must never turn a successful user operation into a 500.
            return False
    return True


def operation_for_request(method, path, mapping_session=None, bulk_workspace=None, request_id=None,
                          client_operation_id=None):
    """Create and persist a started event for a user-visible operation route."""
    normalized = path
    for marker in ('/mapping/', '/bulk-reg/'):
        position = normalized.find(marker)
        if position >= 0:
            normalized = normalized[position:]
            break
    spec = OPERATION_ROUTES.get((method.upper(), normalized))
    if not spec and method.upper() == 'POST' and normalized.startswith('/mapping/files/'):
        kind = normalized.rsplit('/', 1)[-1]
        if kind in {'school', 'dump', 'email_dump'}:
            spec = (f'{kind}_file_upload', f'{kind.replace("_", " ").title()} file upload')
    if not spec:
        return None
    scope = 'bulk' if normalized.startswith('/bulk-reg/') else 'mapping'
    workspace = bulk_workspace if scope == 'bulk' else mapping_session
    if not workspace:
        return None
    operation, label = spec
    event = {
        'operation_id': str(uuid4()), 'workspace_id': workspace_reference(workspace),
        'scope': scope, 'operation': operation, 'status': 'started',
        'started_at': _now(), 'message': f'{label} started.',
    }
    if request_id:
        event['request_id'] = request_id
    client_id = valid_client_operation_id(client_operation_id)
    if client_id:
        event['client_operation_id'] = client_id
    if not _append(event):
        return None
    return event | {'_label': label, '_timer': perf_counter()}


def finish_operation(started, status_code):
    if not started:
        return None
    success = status_code < 400
    event = {
        key: started[key] for key in
        ('operation_id', 'workspace_id', 'scope', 'operation', 'started_at')
    }
    if started.get('client_operation_id'):
        event['client_operation_id'] = started['client_operation_id']
    event.update({
        'status': 'completed' if success else 'failed',
        'finished_at': _now(),
        'duration_ms': round((perf_counter() - started['_timer']) * 1000),
        'message': (f"{started['_label']} completed successfully."
                    if success else f"{started['_label']} failed. Review the message in the application and try again."),
    })
    if started.get('request_id'):
        event['request_id'] = started['request_id']
    _append(event)
    return event


def recent_operations(scope, workspace, limit=10):
    """Return the latest status for up to ``limit`` operations in one workspace."""
    reference = workspace_reference(workspace)
    if not reference or not LOG_PATH.is_file():
        return []
    with LOCK:
        try:
            lines = LOG_PATH.read_text(encoding='utf-8').splitlines()
        except OSError:
            return []
    results = []
    seen = set()
    for line in reversed(lines):
        try:
            event = json.loads(line)
        except (TypeError, json.JSONDecodeError):
            continue
        operation_id = event.get('operation_id')
        if (event.get('scope') == scope and event.get('workspace_id') == reference
                and operation_id and operation_id not in seen):
            seen.add(operation_id)
            results.append({key: value for key, value in event.items()
                            if key not in {'workspace_id', 'scope'}})
            if len(results) >= limit:
                break
    return results


def operations_by_client_id(scope, workspace, client_operation_ids):
    """Return the latest workspace-owned event for each requested browser UUID."""
    requested = {valid_client_operation_id(value) for value in client_operation_ids}
    requested.discard(None)
    reference = workspace_reference(workspace)
    if not requested or not reference:
        return []
    paths = sorted(LOG_PATH.parent.glob('operations-*.jsonl'), reverse=True)
    if LOG_PATH.is_file():
        paths.insert(0, LOG_PATH)
    results = {}
    with LOCK:
        for path in paths:
            try:
                lines = path.read_text(encoding='utf-8').splitlines()
            except OSError:
                continue
            for line in reversed(lines):
                try:
                    event = json.loads(line)
                except (TypeError, json.JSONDecodeError):
                    continue
                client_id = event.get('client_operation_id')
                if (client_id in requested and client_id not in results
                        and event.get('scope') == scope and event.get('workspace_id') == reference):
                    results[client_id] = {key: value for key, value in event.items()
                                          if key not in {'workspace_id', 'scope'}}
            if len(results) == len(requested):
                break
    return [results[value] for value in client_operation_ids if value in results]

