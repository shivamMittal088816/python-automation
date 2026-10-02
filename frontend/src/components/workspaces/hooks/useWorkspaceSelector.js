import { useEffect, useState } from 'react';
import { getInvitedMembers } from '../../../services/invitations/api';
import { listWorkspaces, createWorkspace, selectWorkspace } from '../../../services/workspaces/api';

export function useWorkspaceSelector({ open, role, workflow }) {
  const shared = role === 'editor' || role === 'viewer';
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [spaces, setSpaces] = useState(null);
  const [switching, setSwitching] = useState(false);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setLoading(true);
    setError('');
    listWorkspaces(workflow, controller.signal).then(async data => {
      if (controller.signal.aborted) return;
      setSpaces(data);
      const selected = data.workspaces.find(item => item.id === data.active_workspace_id);
      if (selected?.owned) {
        const people = await getInvitedMembers(workflow, controller.signal);
        if (!controller.signal.aborted) setMembers(people);
      } else setMembers([]);
    }).catch(() => {
      if (!controller.signal.aborted) setError('Could not load workspace details.');
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });
    return () => controller.abort();
  }, [open, shared, workflow, retry]);
  async function changeWorkspace(item) {
    if (switching || (item && item.id === spaces?.active_workspace_id)) return;
    setSwitching(true);
    setError('');
    try {
      if (item) await selectWorkspace(workflow, item.id);
      else await createWorkspace(workflow);
      window.location.assign(workflow === 'mapping' ? '/admission_file_page' : '/bulk-reg');
    } catch (err) {
      setError(err.message || 'Could not change workspace.');
      setSwitching(false);
    }
  }
  return { shared, members, loading, error, spaces, switching, setRetry, changeWorkspace };
}
