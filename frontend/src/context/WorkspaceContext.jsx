import { createContext, useContext, useRef, useState } from 'react';
import { useWorkspaceMetadata } from '../hooks/useWorkspaceMetadata';
import { useWorkspaceInitialization } from '../hooks/useWorkspaceInitialization';
import { useWorkspaceMutation } from '../hooks/useWorkspaceMutation';
import { useWorkspaceState } from '../hooks/useWorkspaceState';
import { useWorkspaceSynchronization } from '../hooks/useWorkspaceSynchronization';
import { WorkspaceSkeleton } from '../components/layout/WorkspaceSkeleton';
import { Alert, Button } from '../components/common/Controls';
import { JoinWorkflowDialog } from '../components/invitations/JoinWorkflowDialog';
import { WorkspaceSelector } from '../components/workspaces/WorkspaceSelector';
import { WorkspaceRemoved } from '../components/workspaces/WorkspaceRemoved';
import { useWorkspaceRemoved } from '../hooks/useWorkspaceRemoved';

const WorkspaceContext = createContext(null);
export const useWorkspace = () => useContext(WorkspaceContext);

export function WorkspaceProvider({ children }) {
  const removed = useWorkspaceRemoved('mapping');
  const { workspace, workspaceRef, publish } = useWorkspaceState();
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);
  const [joinOpen, setJoinOpen] = useState(() => new URLSearchParams(window.location.search).has('invite'));
  const operationActive = useRef(false);
  const synchronization = useWorkspaceSynchronization({ workspaceRef, operationActive, publish, setNotice });
  const { announce, readSequence, refreshPending, refreshWorkspace } = synchronization;
  const { emailSourceKey, metadataKeys, getMappingMetadata, getEmailSourceMetadata } = useWorkspaceMetadata(workspace);
  useWorkspaceInitialization({ revision, publish, announce, refreshPending, setError });
  const run = useWorkspaceMutation({
    workspaceRef, operationActive, readSequence, refreshPending, refreshWorkspace,
    publish, announce, setBusy, setNotice,
  });
  if (removed) return <WorkspaceRemoved />;
  if (!workspace) return error
    ? <main className="mx-auto max-w-xl p-8"><div className="mb-4"><WorkspaceSelector role="viewer" /></div><Alert type="error">{error}</Alert><div className="mt-4 flex flex-wrap gap-2"><Button onClick={() => { setError(''); setRevision(value => value + 1); }}>Retry</Button><Button onClick={() => setJoinOpen(true)}>Join with invitation code</Button></div>{joinOpen && <JoinWorkflowDialog onClose={() => setJoinOpen(false)} initialCode={new URLSearchParams(window.location.search).get('invite') || ''} />}</main>
    : <WorkspaceSkeleton />;
  return <WorkspaceContext.Provider value={{ workspace, id: workspace.workspace_id, busy, run, notice, clearNotice: () => setNotice(null), emailSourceKey, getEmailSourceMetadata, metadataKeys, getMappingMetadata }}>{children}</WorkspaceContext.Provider>;
}
