import { request } from './api';
import { workspacePath } from './admissionMappingApi';
export const emailMappingApi = {
  run: (id, body) => request(`${workspacePath(id)}/email-mapping/run`, { method: 'POST', body }),
  fullNameClass: (id, body) => request(`${workspacePath(id)}/full-name-class-mapping/run`, { method: 'POST', body }),
};
