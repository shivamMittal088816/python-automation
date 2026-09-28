import { request } from "./api";
export const workspacePath = "/mapping";
export const admissionMappingApi = {
  createSession: (school) =>
    request("/mapping/session", {
      method: "POST",
      body: { school_index: school || null },
    }),
  getSession: () => request("/mapping/session"),
  fetchDump: (school_index, revision) =>
    request(`${workspacePath}/student-dump/fetch`, {
      method: "POST",
      body: { school_index },
      revision,
    }),
  schoolDetails: (body, revision) =>
    request(`${workspacePath}/school`, { method: "PATCH", body, revision }),
  map: (body, revision) =>
    request(`${workspacePath}/admission-mapping/run`, {
      method: "POST",
      body,
      revision,
    }),
  configuration: (body, signal) =>
    request(`${workspacePath}/configuration-preview`, {
      method: "POST",
      body,
      signal,
    }),
  results: (stage, filename, params, signal) =>
    request(
      `${workspacePath}/result-previews/${stage}/${encodeURIComponent(filename)}`,
      { params, signal },
    ),
};

/*
 * Purpose: Defines the HTTP operations for the shared admission-mapping workspace.
 * It creates and restores sessions, fetches student dumps, and saves school details.
 * It starts admission matching and requests configuration previews before a run.
 * It also loads paginated result workbooks for the different mapping stages.
 * Every mutating request forwards the workspace revision for conflict detection.
 * Used by: workspace initialization, synchronization, and mutation recovery hooks.
 * AdmissionMappingForm uses it for configuration, dump loading, and mapping runs.
 * EmailMappingPage, FileViewer, and ResultPreview use its read or metadata operations.
 */
