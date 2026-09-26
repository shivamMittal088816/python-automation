// Keep pages usable while an older backend process or saved session is being
// upgraded. Every page can rely on these collections existing.
export function normalizeWorkspace(data) {
  if (!data) return data;
  const record = value => value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const exports = record(data.exports);
  const versions = record(data.export_versions);
  const runColumns = record(data.run_columns);
  return {
    ...data,
    revision: Number.isInteger(data.revision) ? data.revision : 0,
    files: record(data.files),
    settings: record(data.settings),
    exports: {
      admission: record(exports.admission),
      email: record(exports.email),
      full_name_class: record(exports.full_name_class),
    },
    export_versions: {
      admission: record(versions.admission),
      email: record(versions.email),
      full_name_class: record(versions.full_name_class),
    },
    run_columns: {
      admission: record(runColumns.admission),
      email: record(runColumns.email),
      full_name_class: record(runColumns.full_name_class),
    },
  };
}

export const workspaceFingerprint = data => JSON.stringify([data?.workspace_id, data?.revision]);
