const WORKSPACE_CHANNEL_NAME = 'student-mapping-workspace';
const WORKSPACE_CHANGED_MESSAGE = 'workspace-changed';

export function createWorkspaceBroadcastChannel(onWorkspaceChanged) {
  if (typeof BroadcastChannel === 'undefined') {
    return {
      announceWorkspaceChanged() {},
      close() {},
    };
  }

  let channel;
  try {
    channel = new BroadcastChannel(WORKSPACE_CHANNEL_NAME);
  } catch {
    return {
      announceWorkspaceChanged() {},
      close() {},
    };
  }
  channel.onmessage = event => {
    if (event.data === WORKSPACE_CHANGED_MESSAGE) onWorkspaceChanged();
  };

  return {
    announceWorkspaceChanged() {
      try { channel.postMessage(WORKSPACE_CHANGED_MESSAGE); }
      catch { /* Focus and visibility refreshes remain available as a fallback. */ }
    },
    close() {
      try { channel.close(); }
      catch { /* The channel may already be unavailable or closed. */ }
    },
  };
}

/*
 * Purpose: Wraps the browser BroadcastChannel used by the mapping workspace.
 * It publishes a small workspace-changed event instead of copying workspace data.
 * Receiving tabs invoke the supplied callback so they can reload authoritative state.
 * Unsupported, unavailable, or closed channels safely degrade to no-op functions.
 * The returned close method releases the browser channel during React cleanup.
 * Used by: useCrossTabWorkspaceUpdates to connect React lifecycle to the channel.
 * useWorkspaceSynchronization supplies the callback that refreshes server state.
 * Workspace mutations announce changes through the function returned by that hook.
 */
