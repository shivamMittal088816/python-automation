import { request } from './api';
export const workspacePath = () => '/mapping';
export const admissionMappingApi = {
  createSession: school => request('/mapping/session', { method: 'POST', body: { school_index: school || null } }),
  getSession: () => request('/mapping/session'),
  fetchDump: (id, school_index) => request(`${workspacePath(id)}/student-dump/fetch`, { method: 'POST', body: { school_index } }),
  schoolDetails: (id, body) => request(`${workspacePath(id)}/school`, { method: 'PATCH', body }),
  map: (id, body) => request(`${workspacePath(id)}/admission-mapping/run`, { method: 'POST', body }),
  configuration: (id, body, signal) => request(`${workspacePath(id)}/configuration-preview`, { method: 'POST', body, signal }),
  results: (id, stage, filename, params, signal) => request(`${workspacePath(id)}/result-previews/${stage}/${encodeURIComponent(filename)}`, { params, signal }),
};
