import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { admissionMappingApi } from '../services/admissionMappingApi';
import { fileApi } from '../services/fileApi';
import { WorkspaceSkeleton } from '../components/layout/WorkspaceSkeleton';
import { Alert, Button } from '../components/common/Controls';

const WorkspaceContext = createContext(null);
export const useWorkspace = () => useContext(WorkspaceContext);

// Keep pages usable while an older backend process or saved session is being
// upgraded. Every page can rely on these collections existing.
function normalizeWorkspace(data) {
  if (!data) return data;
  return {
    ...data,
    revision: Number.isInteger(data.revision) ? data.revision : 0,
    files: data.files || {},
    settings: data.settings || {},
    exports: {
      admission: {}, email: {}, full_name_class: {},
      ...(data.exports || {}),
    },
    export_versions: {
      admission: {}, email: {}, full_name_class: {},
      ...(data.export_versions || {}),
    },
    run_columns: {
      admission: {}, email: {}, full_name_class: {},
      ...(data.run_columns || {}),
    },
  };
}

export function WorkspaceProvider({ children }) {
  const [workspaceState, setWorkspace] = useState(null);
  // Normalize during render as well as when responses arrive. Vite can preserve
  // pre-update React state during hot reload, and that state may lack revision.
  const workspace = normalizeWorkspace(workspaceState);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);
  const metadataCache = useRef({});
  const workspaceRef = useRef(workspace);
  workspaceRef.current = workspace;
  const operationActive = useRef(false);
  const readSequence = useRef(0);
  const channel = useRef(null);
  const refreshRef = useRef(null);
  const fingerprint = data => JSON.stringify([data?.workspace_id, data?.revision]);
  const announce = () => channel.current?.postMessage('workspace-changed');
  refreshRef.current = async () => {
    if (operationActive.current || !workspaceRef.current) return;
    const sequence = ++readSequence.current;
    try {
      const latest = await admissionMappingApi.getSession();
      if (sequence !== readSequence.current || operationActive.current) return;
      if (fingerprint(latest) !== fingerprint(workspaceRef.current)) {
        setWorkspace(normalizeWorkspace(latest));
        setNotice({ type: 'info', text: 'Workspace updated from another tab. Review your selections before running mapping.' });
      }
    } catch (error) {
      if (sequence === readSequence.current) setNotice({ type: 'warning', text: error.message });
    }
  };
  useEffect(() => {
    if (typeof BroadcastChannel !== 'undefined') {
      channel.current = new BroadcastChannel('student-mapping-workspace');
      channel.current.onmessage = () => refreshRef.current?.();
    }
    const refresh = () => { if (document.visibilityState === 'visible') refreshRef.current?.(); };
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      channel.current?.close();
      window.removeEventListener('focus', refresh);
      document.removeEventListener('visibilitychange', refresh);
      ++readSequence.current;
    };
  }, []);
  const emailSourceKey = JSON.stringify([
    workspace?.workspace_id, workspace?.files.school,
    ...['admission_school_sheet', 'school_name_col',
      'email_input_column', 'email_first_name_column', 'full_name_class_class_column',
      'school_overview_class_column', 'school_overview_section_column']
      .map(key => workspace?.settings[key]),
  ]);
  const metadataKeys = {
    school: emailSourceKey,
    dump: JSON.stringify([workspace?.workspace_id, workspace?.files.dump, workspace?.settings]),
  };
  useEffect(() => {
    for (const kind of Object.keys(metadataCache.current)) {
      if (metadataCache.current[kind].key !== metadataKeys[kind]) delete metadataCache.current[kind];
    }
  }, [metadataKeys.school, metadataKeys.dump]);
  function getMappingMetadata(kind) {
    const key = metadataKeys[kind];
    if (!key) throw new Error('Unknown mapping metadata source.');
    if (metadataCache.current[kind]?.key === key) return metadataCache.current[kind].promise;
    // Share pending requests across navigation. Old responses only populate their own entry.
    const entry = { key };
    const params = { limit: 1 };
    if (kind === 'dump') params.sheet = workspace.settings.admission_dump_sheet;
    entry.promise = fileApi.table(kind, params)
      .then(data => { entry.data = data; return data; })
      .catch(error => {
        if (metadataCache.current[kind] === entry) delete metadataCache.current[kind];
        throw error;
      });
    metadataCache.current[kind] = entry;
    return entry.promise;
  }
  const getEmailSourceMetadata = () => getMappingMetadata('school');
  useEffect(() => {
    let alive = true;
    async function initialize() {
      setError('');
      const school = new URLSearchParams(location.search).get('school');
      let data;
      try { sessionStorage.removeItem('studentMappingSession'); }
      catch { /* Cookie sessions continue to work when browser storage is unavailable. */ }
      try { data = await admissionMappingApi.getSession(); }
      catch (error) { if (![401, 404, 409].includes(error.status)) throw error; }
      // The cookie identifies the active workspace; an old tab's school URL
      // must not replace it when that tab reloads.
      if (!data) { data = await admissionMappingApi.createSession(school); announce(); }
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
