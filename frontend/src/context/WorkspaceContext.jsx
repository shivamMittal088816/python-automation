import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { admissionMappingApi } from '../services/admissionMappingApi';
import { useCrossTabWorkspaceUpdates } from '../hooks/useCrossTabWorkspaceUpdates';
import { useWorkspaceMetadata } from '../hooks/useWorkspaceMetadata';
import { normalizeWorkspace, workspaceFingerprint } from '../utils/workspace';
import { WorkspaceSkeleton } from '../components/layout/WorkspaceSkeleton';
import { Alert, Button } from '../components/common/Controls';

const WorkspaceContext = createContext(null);
export const useWorkspace = () => useContext(WorkspaceContext);

export function WorkspaceProvider({ children }) {
  const [workspaceState, setWorkspace] = useState(null);
  // Normalize during render as well as when responses arrive. Vite can preserve
  // pre-update React state during hot reload, and that state may lack revision.
  const workspace = normalizeWorkspace(workspaceState);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);
  const workspaceRef = useRef(workspace);
  workspaceRef.current = workspace;
  const operationActive = useRef(false);
  const readSequence = useRef(0);
  const refreshWorkspace = async () => {
    if (operationActive.current || !workspaceRef.current) return;
    const sequence = ++readSequence.current;
    try {
      const latest = await admissionMappingApi.getSession();
      if (sequence !== readSequence.current || operationActive.current) return;
      if (workspaceFingerprint(latest) !== workspaceFingerprint(workspaceRef.current)) {
        setWorkspace(normalizeWorkspace(latest));
        setNotice({ type: 'info', text: 'Workspace updated from another tab. Review your selections before running mapping.' });
      }
    } catch (error) {
      if (sequence === readSequence.current) setNotice({ type: 'warning', text: error.message });
    }
  };
  const announce = useCrossTabWorkspaceUpdates(refreshWorkspace, () => { ++readSequence.current; });
  const { emailSourceKey, metadataKeys, getMappingMetadata, getEmailSourceMetadata } = useWorkspaceMetadata(workspace);
  useEffect(() => {
    let alive = true;
    async function initialize() {
      setError('');
      const school = new URLSearchParams(location.search).get('school');
      try { sessionStorage.removeItem('studentMappingSession'); }
      catch { /* Cookie sessions continue to work when browser storage is unavailable. */ }
      const restore = async () => {
        if (!alive) return null;
        let data;
        try { data = await admissionMappingApi.getSession(); }
        catch (error) { if (![401, 404, 409].includes(error.status)) throw error; }
        // Recheck the cookie inside the shared lock: another fresh tab may have
        // created it while this tab waited. Preserve the existing workspace.
        if (!data && alive) { data = await admissionMappingApi.createSession(school); announce(); }
        return data;
      };
      const data = navigator.locks
        ? await navigator.locks.request('student-mapping-session-init', restore)
        : await restore();
      if (alive) setWorkspace(normalizeWorkspace(data));
    }
    initialize().catch(error => alive && setError(error.message));
    return () => { alive = false; };
  }, [revision]);
  async function run(label, action) {
    if (operationActive.current) return null;
    operationActive.current = true;
    ++readSequence.current;
    setBusy(label); setNotice(null);
    try {
      const perform = async () => {
        const data = await action(workspaceRef.current.revision); setWorkspace(normalizeWorkspace(data)); announce();
        if (data.message) setNotice({ type: data.message_type || 'success', text: data.message });
        return data;
      };
      return navigator.locks ? await navigator.locks.request('student-mapping-operation', perform) : await perform();
    } catch (error) {
      if (error.status === 409) {
        try {
          setWorkspace(normalizeWorkspace(await admissionMappingApi.getSession()));
          setNotice({ type: 'warning', text: 'The workspace changed in another tab. Review the updated files and selections, then try again.' });
        } catch (reloadError) {
          setNotice({ type: 'error', text: reloadError.message });
        }
        return null;
      }
      if (error.status === 401 || error.status === 404 && /session/i.test(error.message)) {
        try {
          const school = new URLSearchParams(location.search).get('school');
          const replacement = await admissionMappingApi.createSession(school);
          setWorkspace(normalizeWorkspace(replacement));
          announce();
          setNotice({ type: 'warning', text: 'Your previous session expired or became unavailable. A new session has been created.' });
          return null;
        } catch (recoveryError) {
          setNotice({ type: 'error', text: recoveryError.message });
          return null;
        }
      }
      setNotice({ type: 'error', text: error.message });
      try { setWorkspace(normalizeWorkspace(await admissionMappingApi.getSession())); } catch { /* Keep the original operation error visible. */ }
      return null;
    } finally { operationActive.current = false; setBusy(''); }
  }
  if (!workspace) return error
    ? <main className="mx-auto max-w-xl p-8"><Alert type="error">{error}</Alert><Button onClick={() => { setError(''); setRevision(value => value + 1); }}>Retry</Button></main>
    : <WorkspaceSkeleton />;
  return <WorkspaceContext.Provider value={{ workspace, id: workspace.workspace_id, busy, run, notice, clearNotice: () => setNotice(null), emailSourceKey, getEmailSourceMetadata, metadataKeys, getMappingMetadata }}>{children}</WorkspaceContext.Provider>;
}
