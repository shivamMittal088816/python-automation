import { createContext, useContext, useRef, useState } from 'react';
import { useWorkspaceMetadata } from '../hooks/useWorkspaceMetadata';
import { useWorkspaceInitialization } from '../hooks/useWorkspaceInitialization';
import { useWorkspaceMutation } from '../hooks/useWorkspaceMutation';
import { useWorkspaceState } from '../hooks/useWorkspaceState';
import { useWorkspaceSynchronization } from '../hooks/useWorkspaceSynchronization';
import { WorkspaceSkeleton } from '../components/layout/WorkspaceSkeleton';
import { Alert, Button } from '../components/common/Controls';

const WorkspaceContext = createContext(null);
export const useWorkspace = () => useContext(WorkspaceContext);

export function WorkspaceProvider({ children }) {
  const { workspace, workspaceRef, publish } = useWorkspaceState();
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);
  const operationActive = useRef(false);
  const synchronization = useWorkspaceSynchronization({ workspaceRef, operationActive, publish, setNotice });
  const { announce, readSequence, refreshPending, refreshWorkspace } = synchronization;
  const { emailSourceKey, metadataKeys, getMappingMetadata, getEmailSourceMetadata } = useWorkspaceMetadata(workspace);
  useWorkspaceInitialization({ revision, publish, announce, refreshPending, setError });
  const run = useWorkspaceMutation({
    workspaceRef, operationActive, readSequence, refreshPending, refreshWorkspace,
    publish, announce, setBusy, setNotice,
  });
  if (!workspace) return error
    ? <main className="mx-auto max-w-xl p-8"><Alert type="error">{error}</Alert><Button onClick={() => { setError(''); setRevision(value => value + 1); }}>Retry</Button></main>
    : <WorkspaceSkeleton />;
  return <WorkspaceContext.Provider value={{ workspace, id: workspace.workspace_id, busy, run, notice, clearNotice: () => setNotice(null), emailSourceKey, getEmailSourceMetadata, metadataKeys, getMappingMetadata }}>{children}</WorkspaceContext.Provider>;
}
