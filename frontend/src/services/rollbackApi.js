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

  dumpPage(page) {
    return request('/bulk-reg/rollback/dump/preview', { params: { page } });
  },

  async downloadDump(format) {
    const response = await request('/bulk-reg/rollback/dump/download', {
      params: { file_format: format }, blob: true,
    });
    const disposition = response.headers.get('Content-Disposition') || '';
    const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || `rollback-dump.${format}`;
    const href = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = href;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(href), 1000);
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

  sanityCheck() {
    return request('/bulk-reg/rollback/files/sanity-check', { method: 'POST' });
  },

  clearFile() {
    return request('/bulk-reg/rollback/files', { method: 'DELETE' });
  },
};
