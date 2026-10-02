import { request } from '../api';

export function listWorkspaces(workflow, signal) {
  return request('/workspaces', { params: { workflow }, signal });
}

export function createWorkspace(workflow) {
  return request('/workspaces', { method: 'POST', body: { workflow } });
}

export function selectWorkspace(workflow, workspaceId) {
  return request('/workspaces/select', { method: 'POST', body: { workflow, workspace_id: workspaceId } });
}
