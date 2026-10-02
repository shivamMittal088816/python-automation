import { request } from '../api';

export function listWorkspaces(workflow, signal) {
  return request('/workspaces', { params: { workflow }, signal });
}

export function createWorkspace(workflow, name) {
  return request('/workspaces', { method: 'POST', body: { workflow, name } });
}

export function renameWorkspace(workspaceId, name) {
  return request(`/workspaces/${workspaceId}`, { method: 'PATCH', body: { name } });
}

export function deleteWorkspace(workspaceId) {
  return request(`/workspaces/${workspaceId}`, { method: 'DELETE' });
}

export function selectWorkspace(workflow, workspaceId) {
  return request('/workspaces/select', { method: 'POST', body: { workflow, workspace_id: workspaceId } });
}
