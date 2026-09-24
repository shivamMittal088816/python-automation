# Structure migration

This is a structural refactor of React/Vite plus Python/FastAPI. Node.js remains
frontend tooling. No Node backend, MVC layer, or new processing architecture was added.

## Final layout and responsibilities

```text
student-mapping/
|-- Backend/
|   |-- api/
|   |-- config/
|   |-- models/
|   |-- repositories/
|   |-- routes/
|   |-- schemas/
|   |-- scripts/
|   |-- services/
|   |-- tests/
|   |-- utils/
|   |-- __init__.py
|   `-- main.py
|-- frontend/
|   |-- docs/
|   |-- e2e/
|   |-- src/
|   |   |-- components/
|   |   |-- context/
|   |   |-- hooks/
|   |   |-- pages/
|   |   `-- services/
|   |-- package.json
|   |-- package-lock.json
|   |-- vite.config.js
|   `-- index.html
|-- docs/
|-- storage/
|-- logs/
|-- .env
|-- .env.example
|-- .gitignore
|-- pyproject.toml
|-- uv.lock
|-- cloning.md
`-- README.md
```

| Backend folder | Responsibility |
| --- | --- |
| `routes/` | Existing FastAPI endpoint modules, moved without rewriting handlers. |
| `api/` | Existing HTTP workspace state, storage adapters, and file/serialization helpers. |
| `services/` | Existing mapping, duplicates, account uniqueness, and workbook processing. |
| `repositories/` | Existing SQL queries and database lookups; query text unchanged. |
| `models/` | Existing SQLAlchemy model; columns and table definition unchanged. |
| `config/` | Settings, database engine/session factory, request-scoped session dependency. |
| `schemas/` | Existing Pydantic request and response definitions. |
| `utils/` | File snapshots, logging, response helpers. |
| `scripts/` | CLI and administrative entry points, now under the backend package. |
| `tests/` | Python tests and the isolated browser fixture API. |

`api/` and `routes/` have distinct responsibilities: only endpoint modules moved
into `routes/`. Existing handler internals were not extracted or rewritten.

## Intentionally absent folders

- `jobs/`: no active background/scheduled jobs exist.
- `middlewares/`: the small CORS registration stays in `main.py` unchanged.
- `uploads/`: input handling already belongs to the workflow endpoints; runtime
  data stays under root `storage/`.
- Backend `docs/`: shared architecture is in root `docs/`; no duplicate documentation tree.
- Backend `dist/` and `node_modules/`: Python does not need frontend build/dependency folders.
- Frontend `public/` and `src/utils/`: no current assets/helpers require them.
- `controllers/` and `views/`: no MVC architecture introduced.

No requested source move was blocked. The obsolete database package initializer
and its generated caches were removed only after all tests passed. Runtime data,
root environment, Python dependency files, and storage paths deliberately stayed
in place. Historical Streamlit log filenames remain only in ignored runtime logs.

## Verification

The baseline was recorded after the preliminary page/script/test grouping and
before the explicit Backend/frontend rename and database flattening.

| Check | Baseline | After restructuring |
| --- | --- | --- |
| Python tests | 56 passed | 56 passed |
| React/Playwright tests | 6 passed | 6 passed |
| Vite production build | Passed | Passed, 63 modules transformed |
| Python source compilation | Existing working application | All source compiles |
| OpenAPI contract | Saved complete schema | Identical to baseline |
| FastAPI startup | Fixture server started during baseline E2E | `Backend.main:app` started on 8130; health returned HTTP 200; verification server stopped |
| Vite startup | Started by baseline E2E | Started by `npm run dev -- --port 5174` through E2E |

The default Vite port 5173 was already occupied, so both browser runs used the
existing alternate-port configuration. The suite covers uploads, path loading,
fixture SQL fetching, admission/email/full-name mapping, downloads, searches,
workspace reload, manual-start behavior, and seven pages at desktop/tablet/mobile
widths. Real MySQL access and deployment were not exercised.

A source comparison confirmed 85 application/test files are unchanged apart from
required package/path substitutions. Python test expectations and assertions were
not weakened. Complete OpenAPI equality confirms endpoint URLs, methods, schema
fields, and request/response definitions remain unchanged. CORS and both runtime
storage roots are unchanged. React routes, components, API client behavior, and
workflow remain unchanged by the final rename; the preliminary page grouping only
renamed page components and their imports.

## Imports, configuration and commands

Imports now use `Backend.*`. Models import `Backend.config.database`; SQL
repositories import the same relocated engine. Routes import `Backend.services`,
`Backend.repositories`, `Backend.schemas`, and HTTP support from `Backend.api`.
Test mock targets use the same new paths. Python's case-sensitive package name
`Backend` was verified by importing `Backend.main`, running the CLI tests, and
starting Uvicorn; no compatibility alias or new import-path workaround was added.
The existing direct-script root-path setup was adjusted for the scripts' depth.

The Playwright launcher now calls `Backend/tests/browser_fixture_server.py`, which
reads synthetic fixtures under `frontend/e2e/fixtures`. Vite and environment
variable names stay unchanged. Frontend package/lock files and local environment
moved with the directory. Ignore rules now cover frontend builds/reports and allow
only the intended synthetic fixtures. Root `.env` and `uv.lock` are unchanged.

Backend, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn Backend.main:app --reload --reload-dir Backend
```

Frontend, in another terminal:

```powershell
cd frontend
npm.cmd run dev
```

Python tests and CLI, from the root:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s Backend/tests -v
.\.venv\Scripts\python.exe -m Backend.scripts.admission_mapping_cli --help
```

Frontend checks, from `frontend/`:

```powershell
npm.cmd test -- --config=playwright.feature-removal.config.js
npm.cmd run build
```

Restart any development processes that were launched from old locations using the
new commands. Saved files remain at their existing paths.

## Exact old path to new path map

This table uses locations from the start of the restructuring request. Backend
scripts/tests were first grouped under the Python package before its rename. All
files inside the frontend directory moved together, including local dependencies
and generated builds; those remain ignored and are not listed individually.
The historical doc contents may describe past architecture, but current links and
commands were updated. Old package/path references remain intentionally in this
migration table and ignored audit/runtime artifacts only.

| Old path | New path |
| --- | --- |
| `CLEANUP_REPORT.md` | `docs/CLEANUP_REPORT.md` |
| `CODE_FLOW.md` | `docs/CODE_FLOW.md` |
| `GITHUB_SAFETY.md` | `docs/GITHUB_SAFETY.md` |
| `client/.env` | `frontend/.env` |
| `client/.env.example` | `frontend/.env.example` |
| `client/UI_REFINEMENT.md` | `frontend/docs/UI_REFINEMENT.md` |
| `client/e2e/fixtures/dump.csv` | `frontend/e2e/fixtures/dump.csv` |
| `client/e2e/fixtures/school.csv` | `frontend/e2e/fixtures/school.csv` |
| `client/e2e/presentation.spec.js` | `frontend/e2e/presentation.spec.js` |
| `client/e2e/workflows.spec.js` | `frontend/e2e/workflows.spec.js` |
| `client/index.html` | `frontend/index.html` |
| `client/package-lock.json` | `frontend/package-lock.json` |
| `client/package.json` | `frontend/package.json` |
| `client/playwright.config.js` | `frontend/playwright.config.js` |
| `client/playwright.feature-removal.config.js` | `frontend/playwright.feature-removal.config.js` |
| `client/src/App.jsx` | `frontend/src/App.jsx` |
| `client/src/components/common/Controls.jsx` | `frontend/src/components/common/Controls.jsx` |
| `client/src/components/common/DumpDownload.jsx` | `frontend/src/components/common/DumpDownload.jsx` |
| `client/src/components/common/FileInput.jsx` | `frontend/src/components/common/FileInput.jsx` |
| `client/src/components/common/FileViewer.jsx` | `frontend/src/components/common/FileViewer.jsx` |
| `client/src/components/common/Presentation.jsx` | `frontend/src/components/common/Presentation.jsx` |
| `client/src/components/common/ResultPreview.jsx` | `frontend/src/components/common/ResultPreview.jsx` |
| `client/src/components/common/SchoolIdentity.jsx` | `frontend/src/components/common/SchoolIdentity.jsx` |
| `client/src/components/layout/AppLayout.jsx` | `frontend/src/components/layout/AppLayout.jsx` |
| `client/src/components/tables/DataTable.jsx` | `frontend/src/components/tables/DataTable.jsx` |
| `client/src/context/WorkspaceContext.jsx` | `frontend/src/context/WorkspaceContext.jsx` |
| `client/src/hooks/useRequest.js` | `frontend/src/hooks/useRequest.js` |
| `client/src/hooks/useSessionValue.js` | `frontend/src/hooks/useSessionValue.js` |
| `client/src/index.css` | `frontend/src/index.css` |
| `client/src/main.jsx` | `frontend/src/main.jsx` |
| `client/src/pages/AdmissionMapping/AdmissionFileStep.jsx` | `frontend/src/pages/AdmissionMapping/AdmissionMappingForm.jsx` |
| `client/src/pages/AdmissionMapping/AdmissionMappingPage.jsx` | `frontend/src/pages/AdmissionMapping/AdmissionMappingPage.jsx` |
| `client/src/pages/AdmissionMapping/AdmissionPreviewStep.jsx` | `frontend/src/pages/AdmissionPreview/AdmissionPreviewPage.jsx` |
| `client/src/pages/AdmissionMapping/DumpFileStep.jsx` | `frontend/src/pages/DumpFile/DumpFilePage.jsx` |
| `client/src/pages/AdmissionMapping/SchoolFileStep.jsx` | `frontend/src/pages/SchoolFile/SchoolFilePage.jsx` |
| `client/src/pages/EmailDump/EmailDumpPage.jsx` | `frontend/src/pages/EmailDump/EmailDumpPage.jsx` |
| `client/src/pages/EmailMapping/EmailForm.jsx` | `frontend/src/pages/EmailMapping/EmailForm.jsx` |
| `client/src/pages/EmailMapping/EmailMappingPage.jsx` | `frontend/src/pages/EmailMapping/EmailMappingPage.jsx` |
| `client/src/pages/FullNameClassMapping/FullNameClassMappingPage.jsx` | `frontend/src/pages/FullNameClassMapping/FullNameClassMappingPage.jsx` |
| `client/src/services/admissionMappingApi.js` | `frontend/src/services/admissionMappingApi.js` |
| `client/src/services/api.js` | `frontend/src/services/api.js` |
| `client/src/services/emailMappingApi.js` | `frontend/src/services/emailMappingApi.js` |
| `client/src/services/fileApi.js` | `frontend/src/services/fileApi.js` |
| `client/vite.config.js` | `frontend/vite.config.js` |
| `scripts/__init__.py` | `Backend/scripts/__init__.py` |
| `scripts/admission_mapping/__init__.py` | `Backend/scripts/admission_mapping/__init__.py` |
| `scripts/admission_mapping/admission_file_mapping.py` | `Backend/scripts/admission_mapping/admission_file_mapping.py` |
| `scripts/admission_mapping_cli.py` | `Backend/scripts/admission_mapping_cli.py` |
| `scripts/init_db.py` | `Backend/scripts/init_db.py` |
| `server/__init__.py` | `Backend/__init__.py` |
| `server/api/__init__.py` | `Backend/api/__init__.py` |
| `server/api/file_workflow_helpers.py` | `Backend/api/file_workflow_helpers.py` |
| `server/api/file_workflow_state.py` | `Backend/api/file_workflow_state.py` |
| `server/api/file_workflow_storage.py` | `Backend/api/file_workflow_storage.py` |
| `server/api/file_workflows.py` | `Backend/routes/file_workflows.py` |
| `server/api/student_mapping.py` | `Backend/routes/student_mapping.py` |
| `server/config/__init__.py` | `Backend/config/__init__.py` |
| `server/config/settings.py` | `Backend/config/settings.py` |
| `server/db/database.py` | `Backend/config/database.py` |
| `server/db/dependencies.py` | `Backend/config/dependencies.py` |
| `server/db/models/__init__.py` | `Backend/models/__init__.py` |
| `server/db/models/student_model.py` | `Backend/models/student_model.py` |
| `server/db/repositories/__init__.py` | `Backend/repositories/__init__.py` |
| `server/db/repositories/admission_dump_service.py` | `Backend/repositories/admission_dump_service.py` |
| `server/db/repositories/email_dump_service.py` | `Backend/repositories/email_dump_service.py` |
| `server/db/repositories/user_package_repository.py` | `Backend/repositories/user_package_repository.py` |
| `server/db/repositories/user_student_repository.py` | `Backend/repositories/user_student_repository.py` |
| `server/main.py` | `Backend/main.py` |
| `server/schemas/__init__.py` | `Backend/schemas/__init__.py` |
| `server/schemas/api_response.py` | `Backend/schemas/api_response.py` |
| `server/schemas/file_workflow.py` | `Backend/schemas/file_workflow.py` |
| `server/schemas/student_mapping_student.py` | `Backend/schemas/student_mapping_student.py` |
| `server/services/__init__.py` | `Backend/services/__init__.py` |
| `server/services/admission_mapping/__init__.py` | `Backend/services/admission_mapping/__init__.py` |
| `server/services/admission_mapping/account_duplicates.py` | `Backend/services/admission_mapping/account_duplicates.py` |
| `server/services/admission_mapping/admission_dump_lookup.py` | `Backend/services/admission_mapping/admission_dump_lookup.py` |
| `server/services/admission_mapping/admission_duplicate_checks.py` | `Backend/services/admission_mapping/admission_duplicate_checks.py` |
| `server/services/admission_mapping/admission_file_mapping.py` | `Backend/services/admission_mapping/admission_file_mapping.py` |
| `server/services/admission_mapping/admission_file_reader.py` | `Backend/services/admission_mapping/admission_file_reader.py` |
| `server/services/admission_mapping/admission_input_validation.py` | `Backend/services/admission_mapping/admission_input_validation.py` |
| `server/services/admission_mapping/admission_mapping_pipeline.py` | `Backend/services/admission_mapping/admission_mapping_pipeline.py` |
| `server/services/admission_mapping/admission_name_comparison.py` | `Backend/services/admission_mapping/admission_name_comparison.py` |
| `server/services/admission_mapping/admission_result_exports.py` | `Backend/services/admission_mapping/admission_result_exports.py` |
| `server/services/admission_mapping/admission_row_classification.py` | `Backend/services/admission_mapping/admission_row_classification.py` |
| `server/services/admission_mapping/admission_workbook.py` | `Backend/services/admission_mapping/admission_workbook.py` |
| `server/services/email_file_mapping.py` | `Backend/services/email_file_mapping.py` |
| `server/services/full_name_class_mapping.py` | `Backend/services/full_name_class_mapping.py` |
| `server/services/mapping_account_uniqueness.py` | `Backend/services/mapping_account_uniqueness.py` |
| `server/services/mapping_username_uniqueness.py` | `Backend/services/mapping_username_uniqueness.py` |
| `server/utils/__init__.py` | `Backend/utils/__init__.py` |
| `server/utils/api_responses.py` | `Backend/utils/api_responses.py` |
| `server/utils/file_snapshots.py` | `Backend/utils/file_snapshots.py` |
| `server/utils/logger.py` | `Backend/utils/logger.py` |
| `tests/migration_fixture_server.py` | `Backend/tests/browser_fixture_server.py` |
| `tests/test_admission_duplicates.py` | `Backend/tests/test_admission_duplicates.py` |
| `tests/test_admission_modules.py` | `Backend/tests/test_admission_modules.py` |
| `tests/test_dump_overview.py` | `Backend/tests/test_dump_overview.py` |
| `tests/test_email_file_mapping.py` | `Backend/tests/test_email_file_mapping.py` |
| `tests/test_file_workflow_api.py` | `Backend/tests/test_file_workflow_api.py` |
| `tests/test_full_name_class_mapping.py` | `Backend/tests/test_full_name_class_mapping.py` |
| `tests/test_mapping_account_uniqueness.py` | `Backend/tests/test_mapping_account_uniqueness.py` |

New supporting files: `Backend/routes/__init__.py`, this report, and
`docs/MAPPING_WORKFLOW.md` (the detailed workflow extracted from the former long README).
