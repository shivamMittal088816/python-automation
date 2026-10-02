import { useEffect, useState } from 'react';

// All workspace API errors go through the shared request helper, including
// initialization, mutations, downloads, and background refreshes.
export function useWorkspaceRemoved(workflow) {
  const [removed, setRemoved] = useState(false);
  useEffect(() => {
    const handleRemoved = event => {
      if (event.detail?.workflow === workflow) setRemoved(true);
    };
    window.addEventListener('workspace-removed', handleRemoved);
    return () => window.removeEventListener('workspace-removed', handleRemoved);
  }, [workflow]);
  return removed;
}
