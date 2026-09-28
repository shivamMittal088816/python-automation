import { useCallback, useRef } from 'react';
import { admissionMappingApi } from '../services/admissionMappingApi';
import { workspaceFingerprint } from '../utils/workspace';
import { useCrossTabWorkspaceUpdates } from './useCrossTabWorkspaceUpdates';

export function useWorkspaceSynchronization({ workspaceRef, operationActive, publish, setNotice }) {
  const readSequence = useRef(0);
  const refreshPending = useRef(false);

  const refreshWorkspace = useCallback(async () => {
    if (operationActive.current || !workspaceRef.current) {
      refreshPending.current = true;
      return;
    }
    refreshPending.current = false;
    const sequence = ++readSequence.current;
    try {
      const latest = await admissionMappingApi.getSession();
      if (sequence !== readSequence.current || operationActive.current) return;
      if (workspaceFingerprint(latest) !== workspaceFingerprint(workspaceRef.current)) {
        publish(latest);
        setNotice({ type: 'info', text: 'Workspace updated from another tab. Review your selections before running mapping.' });
      }
    } catch (error) {
      if (sequence === readSequence.current) setNotice({ type: 'warning', text: error.message });
    }
  }, [operationActive, publish, setNotice, workspaceRef]);

  const cancelReads = useCallback(() => { ++readSequence.current; }, []);
  const announce = useCrossTabWorkspaceUpdates(refreshWorkspace, cancelReads);
  return { announce, readSequence, refreshPending, refreshWorkspace };
}

// This hook keeps the mapping workspace in sync with changes made in other tabs.
// It requests the latest server session when a shared update, focus, or visibility event occurs.
// Refreshes wait while a local action is running or the initial workspace is not yet available.
// Request numbers prevent older reads from replacing state after a newer read or action starts.
// It compares workspace fingerprints before publishing changes and showing an update notice.
// It returns refresh controls and an announcement function; failed refreshes show a warning.
// Used by WorkspaceProvider in context/WorkspaceContext.jsx to coordinate shared workspace updates.
// Initialization and mutation hooks use its pending-refresh flag and controls to handle overlapping work.
