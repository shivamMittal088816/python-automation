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

// This hook listens for mapping workspace changes announced by other browser tabs.
// It calls the supplied update function when a message arrives or this tab becomes visible.
// A window-focus listener also requests an update when the user returns to the tab.
// References keep the update and cleanup functions current without recreating listeners.
// When no longer used, it closes the channel, removes listeners, and calls the cleanup function.
// It returns a function that lets this tab announce a workspace change to other tabs.
// Used by useWorkspaceSynchronization.js to trigger a fresh read of the server workspace.
// Its returned announcement function is also passed to initialization and mutation hooks.
