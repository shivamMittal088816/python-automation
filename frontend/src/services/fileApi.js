import { request } from './api';
import { workspacePath } from './admissionMappingApi';
export const fileApi = {
  upload: (id, kind, file) => {
    const body = new FormData(); body.append('file', file);
    return request(`${workspacePath(id)}/files/${kind}`, { method: 'POST', body });
  },
  path: (id, kind, path) => request(`${workspacePath(id)}/files/${kind}/path`, { method: 'POST', body: { path } }),
  table: (id, kind, params, signal) => request(`${workspacePath(id)}/table-previews/${kind}`, { params, signal }),
  download: async (id, kind, params = {}) => {
    const response = await request(`${workspacePath(id)}/downloads/${kind}`, { params, blob: true });
    const disposition = response.headers.get('Content-Disposition') || '';
    const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
    const filename = encoded ? decodeURIComponent(encoded) : params.filename || `${kind}.${params.format || 'csv'}`;
    const href = URL.createObjectURL(await response.blob());
    const link = document.createElement('a'); link.href = href; link.download = filename;
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(href), 1000);
  },
};
