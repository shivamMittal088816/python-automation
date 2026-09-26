import { useCallback, useEffect, useRef } from 'react';
import { createWorkspaceBroadcastChannel } from '../services/cross-tab-broadcast-channel';

export function useCrossTabWorkspaceUpdates(onUpdate, onCleanup) {
  const channel = useRef(null);
  const updateRef = useRef(onUpdate);
  const cleanupRef = useRef(onCleanup);
  updateRef.current = onUpdate;
  cleanupRef.current = onCleanup;

  useEffect(() => {
    channel.current = createWorkspaceBroadcastChannel(() => updateRef.current?.());
    const refreshWhenVisible = () => {
      if (document.visibilityState === 'visible') updateRef.current?.();
    };
    window.addEventListener('focus', refreshWhenVisible);
    document.addEventListener('visibilitychange', refreshWhenVisible);
    return () => {
      channel.current?.close();
      channel.current = null;
      window.removeEventListener('focus', refreshWhenVisible);
      document.removeEventListener('visibilitychange', refreshWhenVisible);
      cleanupRef.current?.();
    };
  }, []);

  return useCallback(() => channel.current?.announceWorkspaceChanged(), []);
}
