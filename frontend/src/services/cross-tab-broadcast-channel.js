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
