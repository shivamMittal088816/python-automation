import { request } from '../api';

export function getInvitedMembers(workflow, signal) {
  return request(`/invitations/members?workflow=${encodeURIComponent(workflow)}`, { signal, workspaceContexts: [workflow] });
}

export function generateInvitation({ workflow, permission }) {
  return request('/invitations', {
    method: 'POST',
    workspaceContexts: workflow === 'both' ? ['mapping', 'bulk_registration'] : [workflow],
    body: {
      workflow,
      permission,
    },
  });
}

export function joinInvitation(token) {
  return request('/invitations/join', {
    method: 'POST',
    body: { token },
  });
}
