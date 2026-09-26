const WORKSPACE_CHANNEL_NAME = 'student-mapping-workspace';
const WORKSPACE_CHANGED_MESSAGE = 'workspace-changed';

export function createWorkspaceBroadcastChannel(onWorkspaceChanged) {
  if (typeof BroadcastChannel === 'undefined') {
    return {
      announceWorkspaceChanged() {},
      close() {},
    };
  }

  const channel = new BroadcastChannel(WORKSPACE_CHANNEL_NAME);
  channel.onmessage = event => {
    if (event.data === WORKSPACE_CHANGED_MESSAGE) onWorkspaceChanged();
  };

  return {
    announceWorkspaceChanged() {
      channel.postMessage(WORKSPACE_CHANGED_MESSAGE);
    },
    close() {
      channel.close();
    },
  };
}
