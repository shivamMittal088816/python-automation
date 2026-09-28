import { request } from './api';
import { workspacePath } from './admissionMappingApi';
export const fileApi = {
  clear: (kind, revision) => request(`${workspacePath}/files/${kind}/clear`, { method: 'POST', revision }),
  upload: (kind, file, revision) => {
    const body = new FormData(); body.append('file', file);
    return request(`${workspacePath}/files/${kind}`, { method: 'POST', body, revision });
  },
  path: (kind, path, revision) => request(`${workspacePath}/files/${kind}/path`, { method: 'POST', body: { path }, revision }),
  table: (kind, params, signal) => request(`${workspacePath}/table-previews/${kind}`, { params, signal }),
  download: async (kind, params = {}) => {
    const response = await request(`${workspacePath}/downloads/${kind}`, { params, blob: true });
    const disposition = response.headers.get('Content-Disposition') || '';
    const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
    const filename = encoded ? decodeURIComponent(encoded) : params.filename || `${kind}.${params.format || 'csv'}`;
    const href = URL.createObjectURL(await response.blob());
    const link = document.createElement('a'); link.href = href; link.download = filename;
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(href), 1000);
  },
};

/*
 * Purpose: Centralizes file operations belonging to the shared mapping workspace.
 * It uploads, loads by path, clears, previews, and downloads each supported file kind.
 * Preview calls accept paging/search parameters and an AbortSignal for cancellation.
 * Download reads the server filename, creates a temporary object URL, and clicks it.
 * Mutating methods include the current revision to protect against stale-tab writes.
 * Used by: FileInput and ClearMappingFileButton for file lifecycle actions.
 * FileViewer, ResultPreview, DumpDownload, and SidebarDownloadButton use read/downloads.
 * useWorkspaceMetadata uses table previews to discover columns and mapping suggestions.
 */
