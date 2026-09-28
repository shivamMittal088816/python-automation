import { request } from './api';

const withSessionLock = action => navigator.locks
  ? navigator.locks.request('bulk-registration-session', action)
  : action();

export const bulkRegistrationApi = {
  async getWorkspace() {
    try { return await request('/bulk-reg/workspace'); }
    catch (error) { if (error.status !== 409) throw error; }
    // Recheck the current cookie under the same lock used by reset. Another
    // tab may already have recovered or reset the session since the first read.
    return withSessionLock(async () => {
      try { return await request('/bulk-reg/workspace'); }
      catch (error) { if (error.status !== 409) throw error; }
      return request('/bulk-reg/workspace', { method: 'POST' });
    });
  },

  verifySchool(schoolIndex, revision) {
    return request('/bulk-reg/school', {
      method: 'POST', body: { school_index: schoolIndex }, revision,
    });
  },

  uploadFile(file, revision) {
    const body = new FormData();
    body.append('file', file);
    return request('/bulk-reg/files', { method: 'POST', body, revision });
  },

  loadPath(path, revision) {
    return request('/bulk-reg/files/path', { method: 'POST', body: { path }, revision });
  },

  selectSheet(sheet, revision) {
    return request('/bulk-reg/files/stored', { method: 'POST', body: { sheet }, revision });
  },

  convert({ schoolIndex, format, page, sheet, revision }) {
    const body = new FormData();
    body.append('school_index', schoolIndex);
    body.append('file_format', format);
    if (format === 'preview') body.append('page', String(page));
    if (sheet != null) body.append('sheet', sheet);
    return request('/bulk-reg/convert', {
      method: 'POST', body, blob: format !== 'preview', revision,
    });
  },

  outputPage(page) {
    return request('/bulk-reg/output', { params: { page } });
  },

  inputPage(page) {
    return request('/bulk-reg/files/input', { params: { page } });
  },

  verifyUsernames() {
    return request('/bulk-reg/output/verify-usernames');
  },

  verifyEmails() {
    return request('/bulk-reg/output/verify-emails');
  },

  clearFile(revision) {
    return request('/bulk-reg/file', { method: 'DELETE', revision });
  },

  resetWorkspace(revision) {
    return withSessionLock(() => request('/bulk-reg/workspace', { method: 'DELETE', revision }));
  },
};
