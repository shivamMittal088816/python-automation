import { consumeOperations } from './operationNotifications.js';

const STORAGE_KEY = 'pending-operation-requests';
const MAX_PENDING_PER_WORKSPACE = 20;
const MAX_WORKSPACES = 20;
const MISSING_GRACE_MS = 5000;

function store() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    if (!value || Array.isArray(value) || typeof value !== 'object') return {};
    return Object.fromEntries(Object.entries(value).map(([scope, entries]) => [
      scope, Array.isArray(entries) ? entries.filter(item => item?.client_operation_id).slice(-MAX_PENDING_PER_WORKSPACE) : [],
    ]));
  } catch {
    return {};
  }
}

function save(value) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(value)); }
  catch { /* The upload can continue when browser storage is unavailable. */ }
}

export function pendingOperations(scope) {
  return scope ? store()[scope] || [] : [];
}

export function beginPendingUpload(scope, operation, file) {
  if (!scope || !crypto?.randomUUID) return null;
  const entry = {
    client_operation_id: crypto.randomUUID(),
    operation,
    file_name: String(file?.name || 'selected file').slice(0, 255),
    file_size: Number.isFinite(file?.size) ? file.size : null,
    status: 'sending',
    started_at: new Date().toISOString(),
  };
  const value = store();
  const entries = (value[scope] || []).filter(item => item.client_operation_id !== entry.client_operation_id);
  delete value[scope];
  value[scope] = [...entries, entry].slice(-MAX_PENDING_PER_WORKSPACE);
  const scopes = Object.keys(value);
  scopes.slice(0, Math.max(0, scopes.length - MAX_WORKSPACES)).forEach(key => delete value[key]);
  save(value);
  return entry.client_operation_id;
}

export function removePendingOperation(scope, clientOperationId) {
  if (!scope || !clientOperationId) return;
  const value = store();
  if (!value[scope]) return;
  value[scope] = value[scope].filter(item => item.client_operation_id !== clientOperationId);
  if (!value[scope].length) delete value[scope];
  save(value);
}

export function reconcilePendingOperations(scope, backendEvents, { markMissing = true } = {}) {
  const pending = pendingOperations(scope);
  if (!pending.length) return null;
  const byClientId = new Map((Array.isArray(backendEvents) ? backendEvents : [])
    .filter(event => event?.client_operation_id)
    .map(event => [event.client_operation_id, event]));
  const now = Date.now();
  const resolved = [];
  for (const item of pending) {
    const event = byClientId.get(item.client_operation_id);
    if (event) {
      resolved.push(event);
      if (['completed', 'failed', 'interrupted'].includes(event.status)) {
        removePendingOperation(scope, item.client_operation_id);
      }
      continue;
    }
    if (!markMissing) continue;
    const age = now - new Date(item.started_at).getTime();
    if (!Number.isFinite(age) || age < MISSING_GRACE_MS) continue;
    removePendingOperation(scope, item.client_operation_id);
    resolved.push({
      operation_id: `client:${item.client_operation_id}`,
      client_operation_id: item.client_operation_id,
      operation: item.operation,
      status: 'interrupted',
      started_at: item.started_at,
      message: `The server did not confirm receiving ${item.file_name}. Please upload the file again.`,
    });
  }
  return consumeOperations(resolved, scope);
}
