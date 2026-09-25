import { request } from './api';
import { workspacePath } from './admissionMappingApi';

export const runEmailMapping = (body, revision) =>
  request(`${workspacePath}/email-mapping/run`, { method: 'POST', body, revision });

export const runFullNameClassMapping = (body, revision) =>
  request(`${workspacePath}/full-name-class-mapping/run`, { method: 'POST', body, revision });
