const STORAGE_KEY = 'acknowledged-operation-events';
const MAX_EVENTS_PER_WORKSPACE = 100;
const MAX_WORKSPACES = 20;

function acknowledgmentStore() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    if (Array.isArray(value)) {
      return { legacy: value.filter(item => typeof item === 'string').slice(-MAX_EVENTS_PER_WORKSPACE) };
    }
    if (!value || typeof value !== 'object') return {};
    return Object.fromEntries(Object.entries(value).map(([scope, entries]) => [
      scope, Array.isArray(entries) ? entries.filter(item => typeof item === 'string').slice(-MAX_EVENTS_PER_WORKSPACE) : [],
    ]));
  } catch {
    return {};
  }
}

function acknowledged(scope) {
  const store = acknowledgmentStore();
  // Read the old hash-only entry during migration so an upgrade does not replay
  // notifications that this browser already acknowledged.
  const previousScope = scope.includes(':') ? scope.slice(scope.indexOf(':') + 1) : null;
  return [...(store.legacy || []), ...(previousScope ? store[previousScope] || [] : []), ...(store[scope] || [])];
}

export function acknowledgeOperation(operationId, status = 'completed', scope = 'unscoped') {
  if (!operationId) return;
  try {
    const key = `${operationId}:${status}`;
    const store = acknowledgmentStore();
    const values = (store[scope] || []).filter(value => value !== key);
    // Reinsert the active workspace last so object order acts as simple LRU order.
    delete store[scope];
    store[scope] = [...values, key].slice(-MAX_EVENTS_PER_WORKSPACE);
    const scopes = Object.keys(store).filter(value => value !== 'legacy');
    scopes.slice(0, Math.max(0, scopes.length - MAX_WORKSPACES)).forEach(value => delete store[value]);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch { /* Notifications still work when browser storage is unavailable. */ }
}

export function consumeOperations(events, scope = 'unscoped') {
  const known = new Set(acknowledged(scope));
  const unseen = (Array.isArray(events) ? events : []).filter(event =>
    event?.operation_id && !known.has(`${event.operation_id}:${event.status}`));
  if (!unseen.length) return null;
  unseen.forEach(event => acknowledgeOperation(event.operation_id, event.status, scope));
  const failed = unseen.filter(event => event.status === 'failed').length;
  const uncertain = unseen.filter(event => ['started', 'interrupted'].includes(event.status)).length;
  const completed = unseen.length - failed - uncertain;
  const counts = [
    completed && `${completed} completed`, failed && `${failed} failed`, uncertain && `${uncertain} interrupted or unfinished`,
  ].filter(Boolean).join(', ');
  const type = failed ? 'error' : uncertain ? 'warning' : 'success';
  let text;
  if (unseen.length === 1 && ['started', 'interrupted'].includes(unseen[0].status)) {
    text = `${unseen[0].message} Its final status is unavailable. Check whether results were saved before running it again.`;
  } else if (unseen.length === 1) {
    text = `${unseen[0].message} This operation finished while the page was closed.`;
  } else {
    text = `${unseen.length} operations changed while the page was closed: ${counts}.`;
  }
  return { type, text, events: unseen };
}

