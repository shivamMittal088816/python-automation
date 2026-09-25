const defaultHost = import.meta.env.DEV
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : window.location.origin;
const configuredHost = import.meta.env.PROD
  ? import.meta.env.VITE_PRODUCTION_API_BASE_URL
  : import.meta.env.VITE_API_BASE_URL;
const host = (configuredHost || defaultHost).replace(/\/$/, '');
const prefix = (import.meta.env.VITE_API_PREFIX || '/api/v1').replace(/^\/?/, '/').replace(/\/$/, '');
export const API_BASE_URL = `${host}${prefix}`;

const cleanMessage = value => String(value || '')
  .replace(/&#x20;|&#32;/gi, ' ')
  .replace(/\s+/g, ' ')
  .trim();

export function apiUrl(path, params = {}) {
  const url = new URL(`${API_BASE_URL}/${path.replace(/^\//, '')}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value == null || value === '') return;
    if (Array.isArray(value)) value.forEach(item => url.searchParams.append(key, item));
    else url.searchParams.set(key, String(value));
  });
  return url.toString();
}

export async function request(path, { method = 'GET', body, params, signal, blob = false, revision } = {}) {
  const multipart = body instanceof FormData;
  let response;
  try {
    response = await fetch(apiUrl(path, params), {
      method, signal, credentials: 'include',
      headers: {
        ...(body && !multipart ? { 'Content-Type': 'application/json' } : {}),
        ...(revision !== undefined ? { 'X-Workspace-Revision': String(revision) } : {}),
      },
      body: body ? multipart ? body : JSON.stringify(body) : undefined,
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('Could not reach the API. Check that the backend is running and try again.');
  }
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
  if (payload.success === false) throw new Error(payload.message || 'The operation could not be completed.');
  return payload;
}
