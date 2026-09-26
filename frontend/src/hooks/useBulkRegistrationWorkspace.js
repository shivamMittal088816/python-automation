import { useCallback, useEffect, useRef, useState } from 'react';

const DATABASE = 'bulk-registration';
const CHANNEL = 'bulk-registration-updates';
const EMPTY = { revision: 0, path: '', file: null, source: null, schoolIndex: '', school: null, output: null };

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE, 1);
    request.onupgradeneeded = () => request.result.createObjectStore('workspace');
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// One read/write transaction makes revision checks atomic across browser tabs.
function transact(database, patch, expectedRevision) {
  return new Promise((resolve, reject) => {
    const transaction = database.transaction('workspace', patch ? 'readwrite' : 'readonly');
    const store = transaction.objectStore('workspace');
    const read = store.get('current');
    let result, conflict;
    read.onsuccess = () => {
      result = read.result || EMPTY;
      if (!patch) return;
      if (expectedRevision !== undefined && expectedRevision !== result.revision) {
        conflict = new Error('Bulk registration changed in another tab. Review the latest values and try again.');
        transaction.abort();
        return;
      }
      result = { ...result, ...patch, revision: result.revision + 1 };
      store.put(result, 'current');
    };
    transaction.oncomplete = () => resolve(result);
    transaction.onabort = transaction.onerror = () => reject(conflict || transaction.error || new Error('Could not save bulk registration.'));
  });
}

export function useBulkRegistrationWorkspace() {
  const [state, setState] = useState(EMPTY);
  const [ready, setReady] = useState(false);
  const [storageError, setStorageError] = useState('');
  const database = useRef(null);
  const channel = useRef(null);
  const current = useRef(EMPTY);
  const pendingEdits = useRef(new Map());
  const apply = useCallback(next => {
    // A focus refresh of the same revision must preserve file identity (and dialogs).
    if (next.revision > current.current.revision) {
      current.current = next;
    }
    // Keep newer keystrokes visible while older IndexedDB writes finish.
    setState(Object.assign({}, current.current, ...pendingEdits.current.values()));
  }, []);
  const refresh = useCallback(async () => {
    if (!database.current) return;
    try { apply(await transact(database.current)); setStorageError(''); setReady(true); }
    catch { setReady(false); setStorageError('Could not read the shared bulk registration workspace. Reload to retry.'); }
  }, [apply]);

  useEffect(() => {
    let active = true;
    openDatabase().then(async db => {
      if (!active) { db.close(); return; }
      database.current = db;
      const initial = await transact(db);
      if (active) { apply(initial); setReady(true); }
    }).catch(() => {
      if (active) setStorageError('Browser storage is unavailable. Enable site storage and reload to use bulk registration.');
    });
    if (typeof BroadcastChannel !== 'undefined') {
      try {
        channel.current = new BroadcastChannel(CHANNEL);
        channel.current.onmessage = refresh;
      } catch { /* Storage events and focus refresh remain available. */ }
    }
    const onStorage = event => { if (event.key === CHANNEL) refresh(); };
    const onVisible = () => { if (document.visibilityState === 'visible') refresh(); };
    window.addEventListener('storage', onStorage);
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      active = false;
      channel.current?.close(); channel.current = null;
      database.current?.close(); database.current = null;
      window.removeEventListener('storage', onStorage);
      window.removeEventListener('focus', refresh);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [apply, refresh]);

  const update = useCallback(async (patch, expectedRevision, optimistic = false) => {
    if (!database.current) throw new Error('The shared workspace is not ready yet.');
    const token = Symbol();
    if (optimistic) {
      pendingEdits.current.set(token, patch);
      apply(current.current);
    }
    try {
      const next = await transact(database.current, patch, expectedRevision);
      pendingEdits.current.delete(token);
      apply(next);
      try { channel.current?.postMessage(next.revision); } catch { /* Use fallback notifications. */ }
      // Fallback for browsers without BroadcastChannel; no student data goes here.
      try { localStorage.setItem(CHANNEL, `${next.revision}:${Date.now()}`); } catch { /* Focus refresh remains available. */ }
      return next.revision;
    } catch (error) {
      pendingEdits.current.delete(token);
      apply(current.current);
      await refresh();
      throw error;
    }
  }, [apply, refresh]);

  return { state, ready, storageError, update, current };
}
