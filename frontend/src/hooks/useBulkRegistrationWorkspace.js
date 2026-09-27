import { useCallback, useEffect, useRef, useState } from 'react';
import { bulkRegistrationApi } from '../services/bulkRegistrationApi';

const CHANNEL = 'bulk-registration-updates';
const EMPTY = { workspace_id: null, revision: 0, path: '', file: null, source: null, schoolIndex: '', school: null, output: null };

export function useBulkRegistrationWorkspace() {
  const [state, setState] = useState(EMPTY);
  const [ready, setReady] = useState(false);
  const [storageError, setStorageError] = useState('');
  const channel = useRef(null);
  const saved = useRef(EMPTY);
  const drafts = useRef({});
  const readSequence = useRef(0);

  const publish = useCallback(result => {
    if (saved.current.workspace_id && saved.current.workspace_id !== result.workspace_id) {
      drafts.current = {};
    }
    saved.current = { ...EMPTY, ...result };
    setState({ ...saved.current, ...drafts.current });
  }, []);

  const refresh = useCallback(async () => {
    const sequence = ++readSequence.current;
    try {
      const result = await bulkRegistrationApi.getWorkspace();
      if (sequence !== readSequence.current) return;
      if (result.workspace_id === saved.current.workspace_id && result.revision < saved.current.revision) return;
      // An unchanged read must preserve selected output pages and open dialogs.
      if (result.workspace_id !== saved.current.workspace_id || result.revision !== saved.current.revision) {
        publish(result);
      }
      setStorageError('');
      setReady(true);
    } catch (error) {
      if (sequence !== readSequence.current) return;
      setReady(false);
      setStorageError(`Could not load the bulk registration workspace. ${error.message} Reload to retry.`);
    }
  }, [publish]);

  useEffect(() => {
    refresh();
    if (typeof BroadcastChannel !== 'undefined') {
      try {
        channel.current = new BroadcastChannel(CHANNEL);
        channel.current.onmessage = refresh;
      } catch { /* Focus refresh remains available. */ }
    }
    window.addEventListener('focus', refresh);
    return () => {
      ++readSequence.current;
      channel.current?.close(); channel.current = null;
      window.removeEventListener('focus', refresh);
    };
  }, [refresh]);

  const beginOperation = useCallback(() => {
    ++readSequence.current;
    return saved.current.workspace_id;
  }, []);

  const replace = useCallback((result, { origin, committed = [], reset = false, announce = true } = {}) => {
    if ((origin && origin !== saved.current.workspace_id)
        || (!reset && result.workspace_id === saved.current.workspace_id && result.revision < saved.current.revision)) {
      throw new Error('Bulk registration changed in another tab or request. Review the updated workspace and try again.');
    }
    ++readSequence.current;
    if (reset) drafts.current = {};
    else for (const key of committed) delete drafts.current[key];
    publish(result);
    // An accepted operation response supersedes an earlier failed refresh.
    setStorageError('');
    setReady(true);
    if (announce) {
      try { channel.current?.postMessage(result.revision); } catch { /* Focus refresh remains available. */ }
    }
  }, [publish]);

  const edit = useCallback(patch => {
    drafts.current = { ...drafts.current, ...patch };
    setState({ ...saved.current, ...drafts.current });
  }, []);

  return { state, ready, storageError, replace, edit, refresh, beginOperation };
}
