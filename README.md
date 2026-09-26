# Student Mapping

A React and FastAPI application for matching school records with existing student
accounts. It supports admission-number, email, and full-name/class workflows,
provides paginated previews, and exports mapping results as CSV or Excel files.

## What it does

- Loads school and dump data from CSV/XLSX files or fetches a dump from MySQL.
- Maps students by admission number, email, or full name plus class.
- Separates results into **Matched**, **Review**, and **Not matched** groups.
- Provides searchable, paginated source and result previews.
- Preserves workflow state while users move between mapping pages.
- Stores source and result bytes as content-addressed `.bin` snapshots.
- Rejects stale concurrent edits with workspace revisions instead of overwriting them.
- Synchronizes successful workspace changes between tabs using `BroadcastChannel`.
- Downloads all currently available mapping groups in one multi-sheet Excel workbook.
- Expires inactive workflow sessions after 24 hours.

Mapping is read-only with respect to the main SQL database: classifications are
not written back automatically.

## Technology

| Layer | Technology |
| --- | --- |
| Frontend | React 19, React Router, Vite |
| Backend | Python 3.12, FastAPI, SQLAlchemy, pandas |
| Database | MySQL |
| Files | CSV and XLSX |
| Testing | Python `unittest` and Playwright |

## Project structure

```text
python-api/
├── Backend/
│   ├── api/             # Session, snapshot and response infrastructure
│   ├── config/          # Environment and database configuration
│   ├── repositories/    # SQL data access
│   ├── routes/          # FastAPI endpoints
│   ├── services/        # Mapping logic
│   ├── tests/           # Backend and API tests
│   └── main.py          # FastAPI application
├── frontend/
│   ├── src/             # React application
│   └── e2e/             # Playwright scenarios and synthetic fixtures
├── docs/                # Architecture and workflow documentation
├── storage/             # Private runtime sessions; ignored by Git
├── .env.example         # Backend configuration template
├── pyproject.toml
└── uv.lock
```

## Requirements

- Python `3.12`
- [uv](https://docs.astral.sh/uv/)
- Node.js `22.12` or newer
- npm
- MySQL access for SQL dump fetching and database-backed email lookup

## Local setup

From the repository root in PowerShell:

```powershell
uv sync --frozen
Copy-Item .env.example .env

Set-Location frontend
npm.cmd ci
Copy-Item .env.example .env
Set-Location ..
```

Fill the root `.env` with your database connection values. Never place database
credentials in `frontend/.env` or commit a populated environment file.

For local HTTP development, use:

```dotenv
SESSION_COOKIE_SECURE=false
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Production must use HTTPS and `SESSION_COOKIE_SECURE=true`.

## Production deployment

Build the frontend once, then let FastAPI serve the compiled SPA and API from the
same origin. Do not run the Vite development server in production.

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run build
Set-Location ..

$env:SERVE_FRONTEND = 'true'
.\.venv\Scripts\python.exe -m uvicorn Backend.main:app --host 0.0.0.0 --port 8000
```

Open the HTTPS URL handled by the production reverse proxy. Direct URLs such as
`/email_mapping_page` return the compiled `index.html`, so refresh and bookmarks
work. Hashed `/assets/` files receive immutable caching; HTML is revalidated.
Production bundles use the current page origin for `/api/v1` by default, preventing
a developer `frontend/.env` URL from being embedded. Set
`VITE_PRODUCTION_API_BASE_URL` only for an intentional cross-origin deployment.

Startup fails clearly when `SERVE_FRONTEND=true` but `frontend/dist` is missing.

## Run locally

Start the backend from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn Backend.main:app --reload --reload-dir Backend
```

Start the frontend in another terminal:

```powershell
Set-Location frontend
npm.cmd run dev
```

| URL | Purpose |
| --- | --- |
| `http://127.0.0.1:5173` | React application |
| `http://127.0.0.1:8000/` | API health check |
| `http://127.0.0.1:8000/docs` | Interactive API documentation |

If the database is unavailable, the API still starts and file-only workflows
remain usable. SQL-dependent features report a database error until connectivity
is restored.

## Workflow

```text
School file + student dump
            ↓
   Admission-number mapping
            ↓
 Matched / Review / Not matched
            ↓
 Email or full-name/class follow-up
            ↓
     Preview and download
```

1. Load a school file.
2. Upload a dump or fetch it using the school index.
3. Select the relevant columns and run admission mapping.
4. Review the generated result groups.
5. Optionally process remaining records through email or full-name/class mapping.
6. Use **Download mapping results** in the sidebar to download all currently
   available groups as separate sheets in one Excel workbook.

Students without admission numbers cannot participate in admission-number matching
and are classified for follow-up rather than silently removed. A failed SQL fetch
does not replace the currently loaded dump or its existing results.

### Input file limits

Browser uploads and files loaded through a backend file path accept CSV or XLSX
files up to **100 MB** (`MAX_UPLOAD_BYTES=104857600`). The limit applies to the
complete file, not to each worksheet. There is currently no separate row-count
limit, so the number of accepted records depends on the file size and available
server memory. SQL dumps fetched by school index do not pass through this upload
limit.

### Download all mapping results

The sidebar download becomes available as soon as at least one mapping stage has
completed. It includes only the stages currently available:

- Admission: `Admission Matched`, `Admission Review`, and `Admission Not Matched`.
- Email: `Email Matched` and `Email Review`.
- Full Name + Class: `Class Matched`, `Class Review`, and `Final Not Matched`.

The workbook is named
`automation-<school-index>-<school-name>.xlsx`. Each result group remains in its
own worksheet because mapping stages have different output columns.

See [Mapping workflow](docs/MAPPING_WORKFLOW.md) for matching rules and data flow.

## Sessions and stored files

The browser receives an HTTP-only session cookie; the session identifier is not
carried in mapping API URLs. The backend stores each workflow under:

```text
storage/temp/workflow_sessions/<session-id>/
├── state.json
└── <sha256>.bin
```

`state.json` links logical inputs and exports to their content-addressed snapshots.
Unchanged bytes reuse the same hash, while changed results receive new snapshot
references. Snapshots that are no longer referenced are removed after a manifest is
published. Sessions inactive for 24 hours are removed with their complete folder.

Mutation requests must send the revision returned by `GET /session` in the
`X-Workspace-Revision` header. The API returns `409 Conflict` for a stale revision;
the browser refreshes to the latest workspace state and asks the user to retry.
Read-only requests do not advance the revision or rewrite the session manifest.
Mapping responses include `X-Request-ID` and `Server-Timing` headers for tracing and
latency monitoring.

### Cross-tab synchronization

Tabs that share the session cookie also share the active workflow. After a
successful mutation, the initiating tab publishes a `workspace-changed` message on
the `student-mapping-workspace` browser `BroadcastChannel`. Other open tabs respond
by fetching `GET /session` and updating their React workspace state when the
workspace ID or revision changed.

The implementation is separated by responsibility:

- `frontend/src/services/cross-tab-broadcast-channel.js` owns the channel name,
  message protocol, browser-support fallback, publishing, and cleanup.
- `frontend/src/hooks/useCrossTabWorkspaceUpdates.js` connects channel messages to
  React and also refreshes when a tab becomes focused or visible.
- `frontend/src/context/WorkspaceContext.jsx` decides when a successful operation
  should be announced and applies refreshed workspace summaries.

`BroadcastChannel` is an immediate-refresh optimization, not the consistency
boundary. Browsers without that API still refresh on focus/visibility changes, and
backend revision checks remain authoritative if a notification is delayed or lost.

See [Session and data flow](docs/SESSION_AND_DATA_FLOW.md) for details.

## API overview

All workflow endpoints use the `/api/v1/mapping` prefix and cookie-based sessions.

| Method and route | Purpose |
| --- | --- |
| `POST /session` | Create a workflow session and set its cookie |
| `GET /session` | Restore the current session |
| `POST /files/{kind}` | Upload a source file |
| `POST /student-dump/fetch` | Fetch dump data for a school index |
| `POST /admission-mapping/run` | Run admission mapping |
| `POST /email-mapping/run` | Run email mapping |
| `POST /full-name-class-mapping/run` | Run full-name/class mapping |
| `GET /table-previews/{kind}` | Search and paginate source data |
| `GET /result-previews/{stage}/{filename}` | Preview a result group |
| `GET /downloads/{kind}` | Download a source or result file |
| `GET /downloads/final-results` | Download available result groups as separate sheets in `automation-<school-index>-<school-name>.xlsx` |

The complete request and response schemas are available through `/docs` while the
backend is running.

## Verification

Run the backend suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s Backend/tests -p "test_*.py"
```

Run the frontend browser tests and production build:

```powershell
Set-Location frontend
npm.cmd test
npm.cmd run build
```

The current verified baseline is 140 backend tests and 18 browser tests passing,
with a successful production frontend build. Browser tests use synthetic fixtures
and isolated workflow storage rather than production data.

## Documentation

- [Complete installation guide](cloning.md)
- [Mapping workflow](docs/MAPPING_WORKFLOW.md)
- [Session and data flow](docs/SESSION_AND_DATA_FLOW.md)
- [Code flow and architecture](docs/CODE_FLOW.md)
- [Automated dump query](docs/AUTOMATED_DUMP_RETRIEVAL_QUERY.md)
- [Website test report](docs/WEBSITE_TEST_REPORT.md)
- [GitHub publishing safety](docs/GITHUB_SAFETY.md)
- [Error handling and production boundaries](docs/ERROR_HANDLING.md)
