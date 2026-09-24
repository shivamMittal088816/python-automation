import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { admissionMappingApi } from '../services/admissionMappingApi';
import { fileApi } from '../services/fileApi';
import { WorkspaceSkeleton } from '../components/layout/WorkspaceSkeleton';
import { Alert, Button } from '../components/common/Controls';

const WorkspaceContext = createContext(null);
export const useWorkspace = () => useContext(WorkspaceContext);

export function WorkspaceProvider({ children }) {
  const [workspace, setWorkspace] = useState(null);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);
  const metadataCache = useRef({});
  const [admissionRevision, setAdmissionRevision] = useState(0);
  const emailSourceKey = JSON.stringify([
    workspace?.workspace_id, workspace?.email_ready, admissionRevision,
    workspace?.files.school, workspace?.files.dump,
    workspace?.export_versions?.admission,
    ...['admission_school_sheet', 'admission_dump_sheet', 'school_name_col',
      'email_input_column', 'email_first_name_column', 'email_full_name_column', 'full_name_class_class_column',
      'school_overview_class_column', 'school_overview_section_column']
      .map(key => workspace?.settings[key]),
  ]);
  const metadataKeys = {
    admission_source: emailSourceKey,
    email_source: JSON.stringify([emailSourceKey, workspace?.export_versions?.email]),
    dump: JSON.stringify([workspace?.workspace_id, workspace?.files.dump, workspace?.settings]),
  };
  useEffect(() => {
    for (const kind of Object.keys(metadataCache.current)) {
      if (metadataCache.current[kind].key !== metadataKeys[kind]) delete metadataCache.current[kind];
    }
  }, [metadataKeys.admission_source, metadataKeys.email_source, metadataKeys.dump]);
  function getMappingMetadata(kind) {
    const key = metadataKeys[kind];
    if (!key) throw new Error('Unknown mapping metadata source.');
    if (metadataCache.current[kind]?.key === key) return metadataCache.current[kind].promise;
    // Share pending requests across navigation. Old responses only populate their own entry.
    const entry = { key };
    const params = { limit: 1 };
    if (kind === 'dump') params.sheet = workspace.settings.admission_dump_sheet;
    entry.promise = fileApi.table(workspace.workspace_id, kind, params)
      .then(data => { entry.data = data; return data; })
      .catch(error => {
        if (metadataCache.current[kind] === entry) delete metadataCache.current[kind];
        throw error;
      });
    metadataCache.current[kind] = entry;
    return entry.promise;
  }
  const getEmailSourceMetadata = () => getMappingMetadata('admission_source');
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
      if (!data || school && data.files.dump?.school_index !== school) data = await admissionMappingApi.createSession(school);
      if (alive) setWorkspace(data);
    }
    initialize().catch(error => alive && setError(error.message));
    return () => { alive = false; };
  }, [revision]);
  async function run(label, action, { invalidateEmailSource = false } = {}) {
    if (busy) return null;
    setBusy(label); setNotice(null);
    if (invalidateEmailSource) {
      delete metadataCache.current.admission_source;
      delete metadataCache.current.email_source;
      setAdmissionRevision(value => value + 1);
    }
    try {
      const data = await action(); setWorkspace(data);
      if (data.message) setNotice({ type: data.message_type || 'success', text: data.message });
      return data;
    } catch (error) {
      if (error.status === 401 || error.status === 409 || error.status === 404 && /session/i.test(error.message)) {
        try {
          const school = new URLSearchParams(location.search).get('school');
          const replacement = await admissionMappingApi.createSession(school);
          setWorkspace(replacement);
          setNotice({ type: 'warning', text: 'Your previous session expired or became unavailable. A new session has been created.' });
          return null;
        } catch (recoveryError) {
          setNotice({ type: 'error', text: recoveryError.message });
          return null;
        }
      }
      setNotice({ type: 'error', text: error.message });
      try { setWorkspace(await admissionMappingApi.getSession(workspace.workspace_id)); } catch { /* Keep the original operation error visible. */ }
      return null;
    } finally { setBusy(''); }
  }
  if (!workspace) return error
    ? <main className="mx-auto max-w-xl p-8"><Alert type="error">{error}</Alert><Button onClick={() => { setError(''); setRevision(value => value + 1); }}>Retry</Button></main>
    : <WorkspaceSkeleton />;
  return <WorkspaceContext.Provider value={{ workspace, id: workspace.workspace_id, busy, run, notice, emailSourceKey, getEmailSourceMetadata, metadataKeys, getMappingMetadata }}>{children}</WorkspaceContext.Provider>;
}
