import { request } from './api';
import { workspacePath } from './admissionMappingApi';
export const emailMappingApi = {
  map: (id, email_column, name_column) => request(`${workspacePath(id)}/email-mapping/run`, { method: 'POST', body: { email_column, name_column } }),
  secondPass: (id, name_column) => request(`${workspacePath(id)}/email-mapping/second-pass`, { method: 'POST', body: { name_column } }),
  fullNameClass: (id, source, name_column, class_column, options = {}) => request(`${workspacePath(id)}/full-name-class-mapping/run`, { method: 'POST', body: { source, name_column, class_column, ...options } }),
};
