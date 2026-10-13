import { request } from './api';

export const rollbackApi = {
  getWorkspace() {
    return request('/bulk-reg/rollback/workspace');
  },

  verifySchool(schoolIndex) {
    return request('/bulk-reg/rollback/school', {
      method: 'POST', body: { school_index: schoolIndex },
    });
  },

  clearSchool() {
    return request('/bulk-reg/rollback/school', { method: 'DELETE' });
  },

  uploadFile(file, sheet) {
    const body = new FormData();
    body.append('file', file);
    if (sheet != null) body.append('sheet', sheet);
    return request('/bulk-reg/rollback/files', { method: 'POST', body });
  },

  selectSheet(sheet) {
    return request('/bulk-reg/rollback/files/sheet', {
      method: 'POST', body: { sheet },
    });
  },

  inputPage(page) {
    return request('/bulk-reg/rollback/files/preview', { params: { page } });
  },

  clearFile() {
    return request('/bulk-reg/rollback/files', { method: 'DELETE' });
  },
};
