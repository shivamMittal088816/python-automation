import { useEffect, useState } from 'react';
import { getInvitedMembers } from '../../../services/invitations/api';
import { listWorkspaces, selectWorkspace } from '../../../services/workspaces/api';

export function useWorkspaceSelector({ open, role, workflow }) {
  const shared = role === 'editor' || role === 'viewer';
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [spaces, setSpaces] = useState(null);
  const [switching, setSwitching] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    listWorkspaces(workflow, controller.signal).then(async data => {
      if (controller.signal.aborted) return;
      setSpaces(data);
      const selected = data.workspaces.find(item => item.id === data.active_workspace_id);
      if (open && selected?.owned) {
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
  useEffect(() => {
    const refresh = () => setRetry(value => value + 1);
    window.addEventListener('focus', refresh);
    return () => window.removeEventListener('focus', refresh);
  }, []);
  function applyName(result) {
    setSpaces(previous => previous ? { ...previous, workspaces: previous.workspaces.map(item =>
      item.id === result.id ? { ...item, name: result.name, needs_name: false } : item) } : previous);
    setRetry(value => value + 1);
  }
  async function changeWorkspace(item) {
    if (switching || (item && item.id === spaces?.active_workspace_id)) return;
    setSwitching(true);
    setError('');
    try {
      await selectWorkspace(workflow, item.id);
      window.location.assign(workflow === 'mapping' ? '/admission_file_page' : '/bulk-reg');
    } catch (err) {
      setError(err.message || 'Could not change workspace.');
      setSwitching(false);
    }
  }
  return { shared, members, loading, error, spaces, switching, setRetry, changeWorkspace, applyName };
}
