const defaultHost = import.meta.env.DEV
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : window.location.origin;
const configuredHost = import.meta.env.PROD
  ? import.meta.env.VITE_PRODUCTION_API_BASE_URL
  : import.meta.env.VITE_API_BASE_URL;
const apiHost = new URL(configuredHost || defaultHost);
const loopbackHosts = new Set(['localhost', '127.0.0.1', '[::1]']);
// Local aliases are different cookie sites. Keep an explicitly configured
// development port, but use the same loopback hostname as the browser.
if (import.meta.env.DEV && loopbackHosts.has(apiHost.hostname) && loopbackHosts.has(window.location.hostname)) {
  apiHost.hostname = window.location.hostname;
}
const host = apiHost.toString().replace(/\/$/, '');
const prefix = (import.meta.env.VITE_API_PREFIX || '/api/v1').replace(/^\/?/, '/').replace(/\/$/, '');
const API_BASE_URL = `${host}${prefix}`;
// Keep each tab's last observed workspace, so a delayed request cannot write to
// a different selection after another tab switches the shared browser session.
const observedWorkspaces = new Map();

const cleanMessage = value => String(value || '')
  .replace(/&#x20;|&#32;/gi, ' ')
  .replace(/\s+/g, ' ')
  .trim();

function apiUrl(path, params = {}) {
  const url = new URL(`${API_BASE_URL}/${path.replace(/^\//, '')}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value == null || value === '') return;
    if (Array.isArray(value)) value.forEach(item => url.searchParams.append(key, item));
    else url.searchParams.set(key, String(value));
  });
  return url.toString();
}

export async function request(path, { method = 'GET', body, params, signal, blob = false, revision, workspaceContexts = [] } = {}) {
  const workflow = path.startsWith('/mapping/') ? 'mapping' : path.startsWith('/bulk-reg/') ? 'bulk_registration' : null;
  const contextHeaders = {};
  for (const context of workspaceContexts) {
    const header = context === 'mapping' ? 'X-Mapping-Workspace'
      : context === 'bulk_registration' ? 'X-Bulk-Registration-Workspace' : null;
    if (header && observedWorkspaces.has(context)) contextHeaders[header] = observedWorkspaces.get(context);
  }
  const multipart = body instanceof FormData;
  let response;
  try {
    response = await fetch(apiUrl(path, params), {
      method, signal, credentials: 'include',
      headers: {
        ...(body && !multipart ? { 'Content-Type': 'application/json' } : {}),
        ...(revision !== undefined ? { 'X-Workspace-Revision': String(revision) } : {}),
        ...(workflow && observedWorkspaces.has(workflow) ? { 'X-Active-Workspace': observedWorkspaces.get(workflow) } : {}),
        ...contextHeaders,
      },
      body: body ? multipart ? body : JSON.stringify(body) : undefined,
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('Could not reach the API. Check that the backend is running and try again.');
  }
  if (!response.ok) {
    if (response.status === 401 && response.headers.get('X-Authentication-Required') === '1') window.dispatchEvent(new Event('auth-expired'));
    let payload = {};
    try { payload = await response.json(); } catch { /* Use the status fallback for non-JSON errors. */ }
    const detail = payload.detail?.message || payload.detail || payload.message;
    const error = new Error(Array.isArray(detail) ? detail.map(item => {
      const field = (item.loc || []).filter(part => !['body', 'query', 'path'].includes(part)).join('.');
      const message = cleanMessage(item.msg);
      return field ? `${field}: ${message}` : message;
    }).join('; ') : cleanMessage(detail) || `Request failed (${response.status}).`);
    error.status = response.status;
    error.workspaceRemoved = response.status === 410 && payload.detail?.code === 'workspace_removed';
    if (workflow && error.workspaceRemoved) {
      window.dispatchEvent(new CustomEvent('workspace-removed', { detail: { workflow } }));
    }
    error.selectionConflict = response.headers.get('X-Workspace-Selection-Conflict') === '1';
    const requestId = response.headers.get('X-Request-ID');
    if (requestId && /^[A-Za-z0-9_.-]{1,64}$/.test(requestId)) {
      error.requestId = requestId;
      error.message += ` (HTTP ${response.status}; request ${requestId})`;
    }
    throw error;
  }
  const activeWorkspace = response.headers.get('X-Active-Workspace');
  if (workflow && activeWorkspace) observedWorkspaces.set(workflow, activeWorkspace);
  if (blob) return response;
  if (response.status === 204) return null;
  let payload;
  try { payload = await response.json(); }
  catch {
    const error = new Error('The API returned an invalid response. Please try again.');
    error.status = response.status;
    throw error;
  }
  if (payload.success === false) throw new Error(payload.message || 'The operation could not be completed.');
  return payload;
}

/*
 * Purpose: Provides the common HTTP foundation used by every frontend API service.
 * It builds the API base URL from development or production environment settings.
 * apiUrl adds query parameters while consistently handling empty and repeated values.
 * request sends JSON or FormData, includes cookies, revisions, and cancellation signals.
 * It normalizes backend, validation, network, blob, and invalid-response handling.
 * Used by: admissionMappingApi, bulkRegistrationApi, emailMappingApi, and fileApi.
 * Feature components call those focused services instead of calling request directly.
 * This keeps transport configuration and error behavior consistent across the UI.
 */
