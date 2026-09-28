import { useCallback } from 'react';
import { admissionMappingApi } from '../services/admissionMappingApi';

function requestedSchool() {
  return new URLSearchParams(location.search).get('school');
}

export function useWorkspaceMutation({
  workspaceRef, operationActive, readSequence, refreshPending, refreshWorkspace,
  publish, announce, setBusy, setNotice,
}) {
  return useCallback(async function run(label, action) {
    if (operationActive.current) return null;
    operationActive.current = true;
    ++readSequence.current;
    setBusy(label);
    setNotice(null);
    try {
      const perform = async () => {
        const data = await action(workspaceRef.current.revision);
        publish(data);
        announce();
        if (data.message) setNotice({ type: data.message_type || 'success', text: data.message });
        return data;
      };
      return navigator.locks
        ? await navigator.locks.request('student-mapping-operation', perform)
        : await perform();
    } catch (error) {
      if (error.status === 409) {
        try {
          publish(await admissionMappingApi.getSession());
          setNotice({ type: 'warning', text: 'The workspace changed in another tab. Review the updated files and selections, then try again.' });
        } catch (reloadError) {
          setNotice({ type: 'error', text: reloadError.message });
        }
        return null;
      }
      if (error.status === 401 || error.status === 404 && /session/i.test(error.message)) {
        try {
          const replacement = await admissionMappingApi.createSession(requestedSchool());
          publish(replacement);
          announce();
          setNotice({ type: 'warning', text: 'Your previous session expired or became unavailable. A new session has been created.' });
          return null;
        } catch (recoveryError) {
          setNotice({ type: 'error', text: recoveryError.message });
          return null;
        }
      }
      setNotice({ type: 'error', text: error.message });
      try { publish(await admissionMappingApi.getSession()); }
      catch { /* Keep the original operation error visible. */ }
      return null;
    } finally {
      operationActive.current = false;
      setBusy('');
      if (refreshPending.current) await refreshWorkspace();
    }
  }, [announce, operationActive, publish, readSequence, refreshPending, refreshWorkspace, setBusy, setNotice, workspaceRef]);
}

// This hook creates the run function used for actions that change the mapping workspace.
// It prevents overlapping actions in this tab, marks the UI busy, and invalidates older reads.
// When available, a browser lock also coordinates actions across tabs before sending the revision.
// Successful actions publish the returned workspace, notify other tabs, and show any server message.
// Conflicts reload the session; expired sessions are recreated; other failures show an error notice.
// Finally, it clears the busy state and performs any refresh that was waiting for the action to finish.
// Used by WorkspaceProvider in context/WorkspaceContext.jsx to expose run through useWorkspace().
// Mapping screens use run for actions such as uploading files, saving settings, and running mappings.
