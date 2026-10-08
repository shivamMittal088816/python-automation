import { acknowledgeOperation } from '../utils/operationNotifications';
import { beginPendingUpload, removePendingOperation } from '../utils/pendingOperations';

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

export async function request(path, { method = 'GET', body, params, signal, blob = false, revision, pendingUpload } = {}) {
  const multipart = body instanceof FormData;
  const clientOperationId = pendingUpload
    ? beginPendingUpload(pendingUpload.scope, pendingUpload.operation, pendingUpload.file)
    : null;
  let response;
  try {
    response = await fetch(apiUrl(path, params), {
      method, signal, credentials: 'include',
      headers: {
        ...(body && !multipart ? { 'Content-Type': 'application/json' } : {}),
        ...(revision !== undefined ? { 'X-Workspace-Revision': String(revision) } : {}),
        ...(clientOperationId ? { 'X-Client-Operation-ID': clientOperationId } : {}),
      },
      body: body ? multipart ? body : JSON.stringify(body) : undefined,
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('Could not reach the API. Check that the backend is running and try again.');
  }
  const responseOperationId = response.headers.get('X-Operation-ID');
  const responseOperationStatus = response.headers.get('X-Operation-Status') || (response.ok ? 'completed' : 'failed');
  const responseOperationWorkspace = response.headers.get('X-Operation-Workspace') || 'unscoped';
  const confirmedClientOperationId = response.headers.get('X-Client-Operation-ID');
  if (clientOperationId && confirmedClientOperationId === clientOperationId) {
    removePendingOperation(pendingUpload.scope, clientOperationId);
  }
  acknowledgeOperation(responseOperationId, responseOperationStatus, responseOperationWorkspace);
  if (!response.ok) {
    let payload = {};
    try { payload = await response.json(); } catch { /* Use the status fallback for non-JSON errors. */ }
    const detail = payload.detail || payload.message;
    const error = new Error(Array.isArray(detail) ? detail.map(item => {
      const field = (item.loc || []).filter(part => !['body', 'query', 'path'].includes(part)).join('.');
      const message = cleanMessage(item.msg);
      return field ? `${field}: ${message}` : message;
    }).join('; ') : cleanMessage(detail) || `Request failed (${response.status}).`);
    error.status = response.status;
    const requestId = response.headers.get('X-Request-ID');
    if (requestId && /^[A-Za-z0-9_.-]{1,64}$/.test(requestId)) {
      error.requestId = requestId;
      error.message += ` (HTTP ${response.status}; request ${requestId})`;
    }
    throw error;
  }
  if (blob) return response;
  if (response.status === 204) return null;
  let payload;
  try { payload = await response.json(); }
  catch {
    const error = new Error('The API returned an invalid response. Please try again.');
    error.status = response.status;
    throw error;
  }
  // The endpoint builds its workspace summary before middleware appends the
  // final event. If that summary still contains this operation's earlier
  // "started" event, acknowledge it together with the final response header.
  // This prevents an outdated recovery warning after an ordinary successful call.
  if (responseOperationId && Array.isArray(payload?.recent_operations)) {
    payload.recent_operations
      .filter(event => event?.operation_id === responseOperationId)
      .forEach(event => acknowledgeOperation(event.operation_id, event.status, responseOperationWorkspace));
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
