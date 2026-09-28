import { useEffect, useRef } from 'react';
import { fileApi } from '../services/fileApi';

export function useWorkspaceMetadata(workspace) {
  const cache = useRef({});
  const emailSourceKey = JSON.stringify([
    workspace?.workspace_id, workspace?.files.school,
    ...['admission_school_sheet', 'school_name_col',
      'email_input_column', 'email_first_name_column', 'full_name_class_class_column',
      'school_overview_class_column', 'school_overview_section_column']
      .map(key => workspace?.settings[key]),
  ]);
  const metadataKeys = {
    school: emailSourceKey,
    dump: JSON.stringify([workspace?.workspace_id, workspace?.files.dump, workspace?.settings]),
  };

  useEffect(() => {
    for (const kind of Object.keys(cache.current)) {
      if (cache.current[kind].key !== metadataKeys[kind]) delete cache.current[kind];
    }
  }, [metadataKeys.school, metadataKeys.dump]);

  function getMappingMetadata(kind) {
    const key = metadataKeys[kind];
    if (!key) throw new Error('Unknown mapping metadata source.');
    if (cache.current[kind]?.key === key) return cache.current[kind].promise;
    const entry = { key };
    const params = { limit: 1 };
    if (kind === 'dump') params.sheet = workspace.settings.admission_dump_sheet;
    entry.promise = fileApi.table(kind, params)
      .then(data => { entry.data = data; return data; })
      .catch(error => {
        if (cache.current[kind] === entry) delete cache.current[kind];
        throw error;
      });
    cache.current[kind] = entry;
    return entry.promise;
  }

  return {
    emailSourceKey,
    metadataKeys,
    getMappingMetadata,
    getEmailSourceMetadata: () => getMappingMetadata('school'),
  };
}

// This hook caches file information needed to configure school and dump mappings.
// Cache keys include the workspace, file details, and settings that affect the requested data.
// A lookup requests a one-row table preview, including the selected dump worksheet when needed.
// Repeated lookups share the same promise so they do not send duplicate requests.
// Changed keys and failed requests remove old cache entries so later lookups can load fresh data.
// It returns the cache keys and lookup functions, including a shortcut for email-source information.
// Used by WorkspaceProvider in context/WorkspaceContext.jsx to share metadata across mapping pages.
// EmailMappingPage.jsx and FullNameClassMappingPage.jsx consume these helpers through useWorkspace().
