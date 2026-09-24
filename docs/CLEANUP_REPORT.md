# Post-migration cleanup report

## 1. Final folder structure

The current source layout is in [README.md](../README.md#project-structure).
The runtime architecture is `frontend/` React/Vite/Tailwind/Router → HTTP → `Backend/`
FastAPI → services → database repositories/models → MySQL. Supporting directories
are `Backend/scripts/`, `tests/`, `storage/` and `logs/`. Framework identification came from
`Backend/main.py`, routes and dependency metadata, not README terminology.

## 2. Deleted source files and safety evidence

45 source files were removed. The dependency audit inspected 157 files, including
111 Python modules, frontend source/configuration, both lockfiles and documentation.
There were no deployment configurations or dynamic loader references requiring
the removed modules. React workflow tests passed before deletion. All nine reusable
UI-independent helper bodies and three generic school-storage function bodies
already had identical active backend implementations. Three tests using those
helpers/storage were redirected before UI deletion; their assertions were preserved.

| Removed group | Why safe |
|---|---|
| Entire `web/` (36 Python files) | Nine pages/components replaced by fixture-verified React/HTTP workflows; no production Backend/script imports; reusable operations already active in backend |
| Root `app.py` | Only dispatched to the retired standalone UI |
| Root `main.py` | Greeting script; no runtime, test, CLI, package or deployment consumer |
| `Backend/scripts/admission_mapping/admission_mapping_cli.py` | Unreferenced import-only alias; canonical CLI and tested public wrapper remain |
| Four unused schemas | Retired upload/validation pipeline or unused student response model; no consumers or OpenAPI registration |
| `Backend/services/base_matcher.py` | Abstract interface for removed matcher pipeline, no subclasses/callers |
| `Backend/services/reviewer_processor.py` | Comment-only placeholder; live Review students updates use existing service/repositories |

Complete deleted-source inventory:

- `app.py`
- `main.py`
- `Backend/scripts/admission_mapping/admission_mapping_cli.py`
- `Backend/schemas/student_schema.py`
- `Backend/schemas/upload_request_schema.py`
- `Backend/schemas/upload_schema.py`
- `Backend/schemas/validation_schema.py`
- `Backend/services/base_matcher.py`
- `Backend/services/reviewer_processor.py`
- `web/__init__.py`
- `web/app.py`
- `web/components/__init__.py`
- `web/components/bulk/__init__.py`
- `web/components/bulk/review_bulk_actions.py`
- `web/components/cards/__init__.py`
- `web/components/cards/review_result_card.py`
- `web/components/dropdown_style.py`
- `web/components/dump_download.py`
- `web/components/filters/__init__.py`
- `web/components/filters/review_filters.py`
- `web/components/panels/__init__.py`
- `web/components/panels/student_review_panel.py`
- `web/components/school_identity.py`
- `web/components/tables/__init__.py`
- `web/components/tables/review_results_table.py`
- `web/legacy_app.py`
- `web/pages/__init__.py`
- `web/pages/admission_mapping/__init__.py`
- `web/pages/admission_mapping/admission_file_page.py`
- `web/pages/admission_mapping/admission_preview_page.py`
- `web/pages/admission_mapping/dump_file_page.py`
- `web/pages/admission_mapping/school_file_page.py`
- `web/pages/email_dump_page.py`
- `web/pages/email_mapping_page.py`
- `web/pages/full_name_class_mapping_page.py`
- `web/pages/jobs_page.py`
- `web/pages/review_page.py`
- `web/services/__init__.py`
- `web/services/admission_mapping/__init__.py`
- `web/services/admission_mapping/admission_school_storage.py`
- `web/services/admission_mapping/admission_session_files.py`
- `web/services/student_mapping_api_service.py`
- `web/utils/__init__.py`
- `web/utils/dump_overview.py`

## 3. Retained legacy-looking files

| File | Reason retained |
|---|---|
| `Backend/scripts/admission_mapping/admission_file_mapping.py` | Public imports and real script/module CLI styles exercised by `test_admission_modules.py` |
| `Backend/scripts/admission_mapping/__init__.py` | Package needed for the supported module entry point |
| `Backend/services/admission_mapping/admission_file_mapping.py` | Public facade imported by active API and business tests |
| `Backend/tests/browser_fixture_server.py` | Actual Playwright web-server entry point; its name does not make it a dead migration helper |
| `Backend/api/file_workflow_helpers.py` | Active search, Preview screen transfers, workbook conversion and overviews; function bodies unchanged |
| `Backend/api/file_workflow_storage.py` | Active school save/restore, staging and rollback; functions unchanged |
| Other file-workflow modules/schema | React depends on their existing HTTP boundary |
| `Backend/scripts/init_db.py` and ORM models | Legitimate database administration and model registration |
| `Backend/repositories/user_package_repository.py` | Independent SQL package/year utility; retained conservatively although no active caller was found |

## 4. Python dependency removal

Removed direct requirements: `streamlit`, `requests`, `duckdb`, `alembic`, `pyarrow`.
Streamlit and requests supported the retired UI/client. No remaining source/test/
script or configuration uses DuckDB or Alembic; no migration configuration exists.
No active Arrow/Parquet API is used; CSV/Excel workflows pass after PyArrow removal.
Required pandas, NumPy, openpyxl, database, FastAPI and serialization packages remain.

uv performed dependency removal and lock regeneration; the lockfile was not manually
edited. The lock shrank from 63 to 32 packages, with no retained version changes.
No frontend or Python package was randomly upgraded. `httptools` and `websockets`
are explicit requirements because Uvicorn previously discovered these installed
transports at runtime. No standard-extra packages were retained unnecessarily.

`uv sync --frozen` initially hit Windows DLL locks. The verified retired UI process
was stopped. The backend was briefly stopped to repair the partially removed HTTP
parser installation, then restarted with the original `Backend.main:app --reload`
command. Its health returns HTTP 200. The final offline frozen sync passed, and
none of the five obsolete packages remains installed. `uv pip check` confirms that
all installed Python dependencies are compatible.

## 5. Frontend dependencies

None removed. All React/Vite/Tailwind/Router/Playwright dependencies have active
source, build or test usage. Babel-based reference inspection found zero unused
imports and all existing API methods used. All frontend source/configuration and
package/lock files are unchanged, and generated build asset names match baseline.
`npm ls --depth=0` also confirms the installed frontend dependency tree is valid.

## 6. Obsolete test removal/replacement

Removed only `test_email_page_handoff_and_missing_column` from the mixed business
test file. Its widget/button/rendering assertions tested the deleted UI and failed
at baseline. Replaced with `test_email_handoff_and_missing_column_validation` in
HTTP API tests: validates successful mapping, source-change invalidation, cleared
email dump/results, missing email suggestion, HTTP 422 and no SQL fetch for invalid
column selection. No business behavior changed to satisfy the old widget assertion.

## 7. Preserved business test coverage

All other existing test methods are retained. Four overview tests now import
`Backend.api.file_workflow_helpers`. Email and full-name/class storage tests now
import `Backend.api.file_workflow_storage`. Matching/classification, duplicates,
leading-zero identifiers, email SQL parameter binding, full-name/class generated
values, per-stage and cross-stage account uniqueness, workbook generation,
safe dump conversion, school persistence/restoration, workspace versions, path
loading, CORS, API validation, Review students persistence and real CLI tests remain.

## 8. Caches and architecture remnants

Removed cache-only `apps/`, `src/`, `Backend/dtos/`, `Backend/handlers/`,
`Backend/models/`, `Backend/repositories/`, and source-directory Python caches.
All non-UI recursive targets were checked to contain only `.pyc`, `.pyo`, temporary
`.pyc.<number>` files or empty directories. All resolved deletion paths were
verified inside the workspace. Existing Python cache ignore patterns remain.
Storage, logs, credentials, node_modules and the Python installation were not
recursively deleted. Package environment changes were handled by uv.

Deleted 201 generated cache files in addition to the 45 source files.

## 9. Compatibility wrappers

Removed the unused CLI alias. Retained the documented/tested public admission
wrapper and backend facade. Both direct/module canonical CLI commands and the
tested original CLI path remain; no useful CLI function was deleted.

## 10–15. Verification results

| Check | Before cleanup | After cleanup |
|---|---|---|
| Python | 56 total, 55 passed, 1 failed (`test_email_page_handoff_and_missing_column`) | 56 total, 56 passed, 0 failed |
| HTTP file-workflow tests | 15 passed | 16 passed |
| React/Edge workflows | 4 passed | 4 passed |
| Production build | Passed | Passed; same asset names and sizes |
| Actual FastAPI startup/health | HTTP 200 | HTTP 200, including restarted original backend |
| Vite startup | Passed as browser-test web server | Passed as browser-test web server |
| Full OpenAPI comparison | Captured | Exactly identical |
| uv metadata/lock check | Original lock | Consistent frozen lock; retained versions unchanged |

Fixtures cover admission, email, full-name/class, all source viewers, Jobs, Review students,
uploads/backend paths, downloads, Preview screens/manual moves, filters, notes/bulk actions for Review students,
refresh/session behavior and responsive navigation. API tests verify school
restoration and disk persistence. Live MySQL/production records were not exercised.

## 16–19. Architecture and behavior confirmations

No active Python source imports Streamlit or deleted UI modules. `web/` is gone
after fixture-backed workflow parity and dependency verification. No active
frontend, backend, script, test or runtime configuration refers to deleted modules.
Historical names appear only in this deletion report. No active matching, SQL,
ORM, API response, workbook, session or storage implementation was removed or
duplicated. Entire OpenAPI matches baseline, React source is unchanged, and
retained backend source matches baseline bytes apart from non-executable comment/
module-documentation edits. No runtime storage or existing log data was deleted.

## 20. Deliberate conservative retentions

`UserPackageRepository` is retained because it contains an independent SQL utility
whose manual/admin use cannot be ruled out from repository callers. The tested
CLI compatibility path remains intentionally supported. Runtime data/logs are
preserved. No other uncertain legacy source was deleted. Temporary dependency-map,
constraint and verification scripts are removed after report generation.
