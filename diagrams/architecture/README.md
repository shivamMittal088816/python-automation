# Current application architecture

Open [the interactive diagram](output/architecture.html) in a browser.
Edit [the architecture specification](specs/architecture.json), then regenerate;
never edit the generated HTML manually. Archify runs during documentation/build
work, outside the application request flow. Deploy only the generated HTML when
a hosting route is added later; this task adds no application route.

## Regenerate from the repository root

```powershell
.\archify.ps1 validate architecture diagrams/architecture/specs/architecture.json --quality showcase --json
if ($LASTEXITCODE -ne 0) { throw 'Architecture validation failed' }
.\archify.ps1 deliver architecture diagrams/architecture/specs/architecture.json diagrams/architecture/output/architecture.html --quality showcase --json
if ($LASTEXITCODE -ne 0) { throw 'Architecture delivery failed' }
.\archify.ps1 visual-check diagrams/architecture/output/architecture.html --json
if ($LASTEXITCODE -ne 0) { throw 'Architecture browser checks did not pass' }
```

Review the generated screenshots after changing the specification. Visual-check
writes a JSON receipt, a contact sheet, and four screenshots beside the HTML.

## Evidence and abstraction

Inspected the local working tree on 2026-09-27. This is a module-level runtime
architecture, not a verified production deployment topology. Arrows show selected
calls and dependencies; responses return through the same API client. They do
not impose a mandatory sequence of mapping stages. Grouped nodes represent code
within the same application, not independently deployed microservices.

| Diagram component | Current source evidence |
| --- | --- |
| React workspace UI | `frontend/src/App.jsx`, `context/WorkspaceContext.jsx`, `hooks/useBulkRegistrationWorkspace.js`, `pages/`, `components/common/ResultPreview.jsx` |
| API service layer | `frontend/src/services/api.js`, `admissionMappingApi.js`, `emailMappingApi.js`, `bulkRegistrationApi.js`, `fileApi.js` |
| FastAPI routers | `backend/app/main.py`, `routes/file_workflows.py`, `routes/file_workflow_routes/`, `routes/bulk_registration/`, `routes/student_mapping.py` |
| Mapping services | `backend/app/services/admission_mapping/`, `email_mapping/`, `full_name_class_mapping/`; invoked by the corresponding mapping routes |
| Workspace and file I/O | `backend/app/api/session_cookie.py`, `file_workflow_state.py`, `file_workflow_session_storage.py`, `file_workflow_snapshots.py`, `services/bulk_registration_storage.py`, `services/final_results_workbook.py`, `utils/workbook_operations.py` |
| Bulk registration | `backend/app/routes/bulk_registration/conversion_routes.py`, `services/bulk_registration.py`, `mappings/bulk_registration/` |
| SQL access / MySQL | `backend/app/repositories/`, `services/bulk_registration.py::fetch_school`, `config/database.py`, `config/dependencies.py` |
| Backend filesystem | Mapping: `backend/storage/temp/workflow_sessions/<uuid>/`; parse staging: `backend/storage/temp/admission_mapping/`; bulk: `backend/storage/bulk_registration/<uuid>/` |

Paths in the frontend UI and client rows after the first entry are relative to
`frontend/src/`; backend entries are relative to `backend/app/`.

The workspace/file node groups parsing, lifecycle, preview and export helpers.
Bulk routes also access their separate disk workspace. The SQL node includes
direct school lookup SQL in the bulk service as well as repositories; it is not
a claim that every database call uses a repository class. MySQL connectivity was
not tested, and no private environment files or student records were needed.

Current `full_name_class_mapping.py` accepts school input, Admission Not Matched,
or Email Not Matched; this supersedes older documentation describing school-only
input. Review is a saved result category with read-only previews, not a separate
review queue. Combined XLSX downloads are assembled from saved result snapshots.
The bulk feature converts and exports registration files; no account-creation
service is inferred.

No cloud provider, load balancer, authentication provider, queue, worker, shared
filesystem service, or production host is asserted. CLI/database initialization
scripts are outside the browser runtime view. Source paths above describe the
inspected working tree; commit-pinned source badges were deliberately omitted
because this diagram is not evidence of a specific published commit.

## Verification receipt

- Diagram type: architecture; installed schema version: 1.
- Validation and atomic delivery: **9/9 showcase, 0 errors, 0 warnings**.
- Browser evidence: **passed** at 1440x900, 1600x1000, 1920x1080, 2048x1320.
- Perceptual review: **passed** for captured light and dark diagram composition,
  labels, routes, cards and viewport containment. Interactive exports and every
  viewer control were not individually exercised.
- Visual correction rounds: **1** (vertical spacing compacted).
- Specification: 5,873 bytes; SHA-256
  `4444688d34253ccb7d8fb095bf67ae6d75c189718e0d9f8d26ce2abac593a3ba`.
- HTML: 812,340 bytes; SHA-256
  `1cceea4aec1d95c4237cbace91e55387ecec8bb7225b0c6c6959947f8e4b6b48`.

The generated `output/architecture.visual-check.json` retains
`visualReview: pending` by design: it records automated browser evidence only.
The separate perceptual review above records inspection of the rendered images.
Hashes and this receipt describe this generation; update them after regeneration.

The files were subsequently moved into `diagrams/architecture/` without changing
the specification or HTML bytes. The original automated receipt retains its
generation-time absolute artifact path; its hash still identifies this HTML.
The next `visual-check` run refreshes the receipt with the new location.
