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
