import { useCallback, useRef, useState } from 'react';
import { normalizeWorkspace } from '../utils/workspace';

export function useWorkspaceState() {
  const [workspaceState, setWorkspace] = useState(null);
  const workspace = normalizeWorkspace(workspaceState);
  const workspaceRef = useRef(workspace);
  workspaceRef.current = workspace;

  const publish = useCallback((data) => {
    const next = normalizeWorkspace({
      ...data,
      role: data.role || (data.workspace_id === workspaceRef.current?.workspace_id ? workspaceRef.current.role : 'owner'),
    });
    workspaceRef.current = next;
    setWorkspace(next);
  }, []);

  return { workspace, workspaceRef, publish };
}

// This hook holds the mapping workspace in React state, starting without a loaded session.
// It passes stored data through normalizeWorkspace so callers receive a consistent structure.
// A reference keeps the latest workspace available to asynchronous code without waiting for a render.
// The publish function normalizes new workspace data and immediately updates that reference.
// It also updates React state so components display the newly published workspace.
// It returns the workspace, its reference, and publish for the other workspace hooks to share.
// Used by WorkspaceProvider in context/WorkspaceContext.jsx as its central workspace state.
// Initialization, synchronization, and mutation hooks publish their server responses through it.
