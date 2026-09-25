import { request } from './api';
export const workspacePath = '/mapping';
export const admissionMappingApi = {
  createSession: school => request('/mapping/session', { method: 'POST', body: { school_index: school || null } }),
  getSession: () => request('/mapping/session'),
  fetchDump: (school_index, revision) => request(`${workspacePath}/student-dump/fetch`, { method: 'POST', body: { school_index }, revision }),
  schoolDetails: (body, revision) => request(`${workspacePath}/school`, { method: 'PATCH', body, revision }),
  map: (body, revision) => request(`${workspacePath}/admission-mapping/run`, { method: 'POST', body, revision }),
  configuration: (body, signal) => request(`${workspacePath}/configuration-preview`, { method: 'POST', body, signal }),
  results: (stage, filename, params, signal) => request(`${workspacePath}/result-previews/${stage}/${encodeURIComponent(filename)}`, { params, signal }),
};
