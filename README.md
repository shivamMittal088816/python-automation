# Student Mapping

Terminology: **Review students** means students who need checking; **Preview screen**
means the screen used to view any result group. The app?s exact status value remains
`Review`; API paths, filenames and code identifiers retain their original names.


A React + FastAPI application for matching school CSV/XLSX records with existing
student accounts using admission numbers, email, or full name and class number.
Use the Preview screen to view Matched, Review students, and Not matched results and download Excel/CSV exports.

Node.js runs React's Vite tooling; the backend remains Python. Streamlit is not required.

## Project structure

```text
student-mapping/
|-- Backend/
|   |-- routes/         # FastAPI endpoint definitions
|   |-- api/            # HTTP workspace, file and serialization support
|   |-- services/       # Mapping algorithms and account checks
|   |-- repositories/   # SQL lookups and persistence queries
|   |-- models/         # SQLAlchemy models
|   |-- config/         # Settings, database engine and request sessions
|   |-- schemas/        # Pydantic request/response definitions
|   |-- utils/          # File snapshots, logging and shared helpers
|   |-- scripts/        # Python CLI and administration tools
|   |-- tests/          # Backend tests and browser fixture API
|   `-- main.py         # FastAPI app and factory
|-- frontend/
|   |-- src/            # React pages, components, hooks and API client
|   |-- e2e/            # Playwright tests and synthetic CSV fixtures
|   |-- docs/           # Frontend UI implementation notes
|   `-- package.json    # Vite scripts and frontend dependencies
|-- docs/               # Architecture, workflow and migration documentation
|-- storage/            # Private runtime files and saved workspaces (ignored)
|-- logs/               # Runtime logs (ignored)
|-- .env.example        # Safe backend configuration template
|-- .gitignore
|-- pyproject.toml
|-- uv.lock
|-- cloning.md          # Complete setup guide
`-- README.md
```

Generated dependencies, builds, Python environments and local `.env` files are
ignored. Runtime files remain outside source folders.

## Mapping API routes

Python route filenames use descriptive `snake_case`; API paths use lowercase
`kebab-case`. The default API prefix is `/api/v1`. Session-specific endpoints
follow `/api/v1/mapping/sessions/{session_id}/{resource}`, with an action suffix
for operations such as `run`, `fetch`, and `reconcile`.

`Backend/routes/file_workflows.py` assembles the routers below from
`Backend/routes/file_workflow_routes/`. Paths in this table are relative to
`/api/v1/mapping/sessions/{session_id}`.

| File | Method and path | Purpose |
| --- | --- | --- |
| `mapping_sessions.py` | `GET` base path; `PUT /settings` | Read session and update settings |
| `duplicate_accounts.py` | `POST /duplicate-accounts/reconcile` | Identify Review students with duplicate accounts across mapping stages |
| `file_inputs.py` | `POST /files/{kind}`; `POST /files/{kind}/path` | Upload or load input files |
| `file_inputs.py` | `POST /student-dump/fetch`; `PATCH /school` | Fetch the SQL dump and update school details |
| `admission_mapping.py` | `POST /admission-mapping/run` | Run admission mapping |
| `admission_mapping.py` | `POST /admission-mapping/move` | Disabled student-move operation (403) |
| `email_mapping.py` | `POST /email-mapping/run` | Run email mapping |
| `full_name_class_mapping.py` | `POST /full-name-class-mapping/run` | Run full name + class mapping |
| `mapping_previews.py` | `GET /table-previews/{kind}`; `GET /result-previews/{stage}/{filename}` | Show inputs and mapping results on the Preview screen |
| `file_downloads.py` | `GET /downloads/{kind}` | Download input files or mapping results |

Create a session with `POST /api/v1/mapping/sessions` (`mapping_sessions.py`).
Health and student browsing remain at `/api/v1/mapping/health` and
`/api/v1/mapping/students` (`student_mapping.py`).

Shared configuration, validation, file-reading, and response helpers live in
`Backend/api/file_workflow_route_helpers.py`. The frontend uses these renamed
endpoints; external clients using the former `/file-workflows` URLs must update.

## Requirements

- Python **3.12** and uv.
- Node.js **22.12 or newer**, with npm.
- Existing compatible MySQL data and credentials for SQL fetching and email lookup.
- Microsoft Edge for the checked-in Windows Playwright configuration.

See [cloning.md](cloning.md) for installation, sample files, platform notes,
environment settings, and troubleshooting.

## Setup

From the repository root in PowerShell:

```powershell
uv sync --frozen
Copy-Item .env.example .env
cd frontend
npm.cmd ci
Copy-Item .env.example .env
cd ..
```

Copy templates only for a new checkout; preserve existing configured `.env` files.
Fill in root `.env` with your database settings. All five `DB_*` fields are required
at startup, even for file-only work. Uploaded-file admission mapping can run without
a live SQL connection; SQL fetching and normal email mapping need the real database.

`frontend/.env` defaults to `VITE_API_BASE_URL=http://127.0.0.1:8000` and
`VITE_API_PREFIX=/api/v1`. Database credentials belong only in the backend environment.

## Run

Backend terminal, from the repository root:

```powershell
cd D:\python-api
.\.venv\Scripts\python.exe -m uvicorn Backend.main:app --reload --reload-dir Backend
```

Frontend terminal, from the repository root:

```powershell
cd D:\python-api\frontend
npm.cmd run dev
```

Frontend commands (run either one from `frontend/`):

- `npm run start`: starts Vite directly.
- `npm run dev`: starts Vite through nodemon, which restarts it when frontend
  configuration or environment files change.

React and CSS edits update automatically through Vite's hot module replacement in
both modes; no manual browser refresh is normally needed. Nodemon does not restart
the entire server for every React edit, allowing React Fast Refresh to preserve
component state where supported. The Python backend still runs in its own terminal.

| Address | Purpose |
| --- | --- |
| http://127.0.0.1:5173 | React application |
| http://127.0.0.1:8000/docs | API documentation |
| http://127.0.0.1:8000/api/v1/mapping/health | API health; does not check MySQL |

Keep both terminals running. Stop each with `Ctrl+C`. Backend settings load from
root `.env`, so start Python from the repository root.

Startup checks MySQL with a read-only `SELECT 1` and logs **Database connected
successfully** only when it succeeds. If the connection fails, a warning appears
and file-only workflows remain available. Uvicorn reports the listening host and
port; with `--reload`, its reloader may print that address before the worker's
database check. These messages appear in the backend terminal.

If SQL fetching reports MySQL error `2003` with Windows error `10061`, the
configured database host/port refused the connection. For local XAMPP, start
**MySQL** in the XAMPP Control Panel before using **Fetch dump data**. Check that
its port matches `DB_PORT` in the private root `.env`. Once MySQL is running,
retry the fetch; restart the backend if you changed `.env` values. This error
occurs before authentication or the admission query executes.

`StatReload detected changes` is expected when editing Python source with
`--reload`. The command above restricts watching to `Backend`, avoiding reloads
caused by changes inside `.venv`. It still reloads for Backend test-file edits.

## Workflow

1. Load the school file and upload a student dump or fetch one by school index.
   SQL fetches select students (`user_type = '0'`) for the entered school and use a
   `LEFT JOIN` to attach paid-table admission numbers. Students without paid records
   remain with blank admissions. Exact normalized duplicates are removed; distinct
   admissions can still produce multiple rows per student. See
   [SQL dump selection and counts](docs/MAPPING_WORKFLOW.md#sql-dump-selection-and-counts).
   An invalid index or
   database error leaves the currently loaded dump and results unchanged.
2. Choose the input columns and click **Start admission mapping**.
3. Open the Preview screen for result groups and download CSV/Excel workbooks.
4. For admission misses, choose the email and first-name columns and run Email
   Pass 1. It compares the selected first name with dump `user_firstname`;
   matching one-character names are sent to Review. Email Pass 2 uses a separately
   selected full-name column and compares sorted full-name characters.
5. Optionally use **1st round mapping** for full-name/class concatenation on either
   remaining Not matched source, then **2nd round mapping** to retry its misses
   using sorted full-name characters and the selected dump class column.

Opening pages does not start mapping. Saved results and workspace selections remain
available across navigation. Preview screens are read-only; manual transfers and standalone
Jobs/Review students pages are unavailable. Mapping does not write classifications back to
SQL. See the [detailed workflow](docs/MAPPING_WORKFLOW.md).

## Verification

Python tests, from the root:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s Backend/tests -v
```

Frontend tests and build, from `frontend/`:

```powershell
npm.cmd test
npm.cmd run build
```

Browser tests start a fixture API on 8123 and Vite on 5173. If your normal frontend
is using 5173, use the alternate configuration on 5174:

```powershell
npm.cmd test -- --config=playwright.feature-removal.config.js
```

Tests use synthetic fixtures and isolated storage rather than live MySQL data.
The browser launcher currently uses Windows Python paths and Microsoft Edge.

## CLI and administration

From the root:

```powershell
.\.venv\Scripts\python.exe -m Backend.scripts.admission_mapping_cli --help
.\.venv\Scripts\python.exe -m Backend.scripts.admission_mapping_cli --school school.csv --dump dump.csv --output results.xlsx
```

Direct execution of `Backend/scripts/admission_mapping_cli.py` is also supported.
`Backend/scripts/init_db.py` is an optional database-writing administration command;
it creates the ORM `students` table, not the external SQL lookup schema. It is not
a normal installation or startup step.

## Documentation

- [Clone and run](cloning.md)
- [Code flow and architecture](docs/CODE_FLOW.md)
- [Mapping workflow](docs/MAPPING_WORKFLOW.md)
- [Structure migration and path map](docs/STRUCTURE_MIGRATION.md)
- [Frontend UI notes](frontend/docs/UI_REFINEMENT.md)
- [GitHub publishing safety](docs/GITHUB_SAFETY.md)
- [Historical cleanup report](docs/CLEANUP_REPORT.md)
