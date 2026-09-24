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
4. Review and download the generated result groups.
5. Optionally process remaining records through email or full-name/class mapping.

Students without admission numbers cannot participate in admission-number matching
and are classified for follow-up rather than silently removed. A failed SQL fetch
does not replace the currently loaded dump or its existing results.

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
references. Sessions inactive for 24 hours are removed with their complete folder.

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

The current verified baseline is 128 backend tests and 18 browser tests passing,
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
