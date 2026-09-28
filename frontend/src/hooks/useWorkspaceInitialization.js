import { useEffect } from 'react';
import { admissionMappingApi } from '../services/admissionMappingApi';

function requestedSchool() {
  return new URLSearchParams(location.search).get('school');
}

export function useWorkspaceInitialization({ revision, publish, announce, refreshPending, setError }) {
  useEffect(() => {
    let alive = true;

    async function initialize() {
      setError('');
      try { sessionStorage.removeItem('studentMappingSession'); }
      catch { /* Cookie sessions continue to work when browser storage is unavailable. */ }

      const restore = async () => {
        if (!alive) return null;
        let data;
        try { data = await admissionMappingApi.getSession(); }
        catch (error) { if (![401, 404, 409].includes(error.status)) throw error; }
        if (!data && alive) {
          data = await admissionMappingApi.createSession(requestedSchool());
          announce();
        }
        return data;
      };

      let data = navigator.locks
        ? await navigator.locks.request('student-mapping-session-init', restore)
        : await restore();
      while (alive && refreshPending.current) {
        refreshPending.current = false;
        data = await admissionMappingApi.getSession();
      }
      if (alive) publish(data);
    }

    initialize().catch(error => alive && setError(error.message));
    return () => { alive = false; };
  }, [announce, publish, refreshPending, revision, setError]);
}

// This hook restores the mapping workspace when the provider starts or initialization is retried.
// It removes an old browser-storage session entry and asks the API for the cookie-backed session.
// If that session is unavailable, it creates one using the school query parameter when present.
// When supported, a browser lock coordinates startup so tabs do not create sessions at the same time.
// It rereads the session if an update arrived during startup, then publishes the current workspace.
// Failures are sent to the error handler, and results are ignored after this effect is cleaned up.
// Used by WorkspaceProvider in context/WorkspaceContext.jsx to prepare the mapping pages.
// The provider shows a loading screen or retry message until initialization succeeds.
