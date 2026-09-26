# Student Mapping

Current startup commands for the updated folders: [Run the project](backend/docs/RUNNING.md).

A React and FastAPI application for mapping school records by admission number,
email, and full name plus class. The repository has two independently deployable
applications:

```text
python-api/
├── frontend/                 # React/Vite site
│   ├── src/
│   ├── e2e/
│   ├── .env.example
│   ├── package.json
│   └── README.md
└── backend/                  # FastAPI service
    ├── app/
    ├── tests/
    ├── docs/
    ├── .env.example
    ├── pyproject.toml
    ├── uv.lock
    └── README.md
```

The frontend folder contains everything needed for the website deployment. The
backend folder contains everything needed for the API deployment. FastAPI no
longer builds or serves the frontend.

## Features

- CSV/XLSX school and dump inputs up to 100 MB.
- Optional student dump retrieval from MySQL by school index.
- Admission, email, and full-name/class mapping stages.
- Matched, Review, and Not Matched result previews and individual downloads.
- Progressive multi-sheet **Download mapping results** workbook.
- Cookie-backed workflows with 24-hour inactivity expiry.
- Same-origin cross-tab synchronization through `BroadcastChannel`.
- Optimistic revision checks that reject stale concurrent changes.

## Local development

After dependency and environment setup, start both services with one command:

```powershell
Set-Location D:\python-api
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-project.ps1
```

Keep that terminal open; Ctrl+C stops both services. The script uses local HTTP
settings without changing `.env` files and writes diagnostics to `logs/`.
If existing servers occupy the default ports, stop them first or use
`-BackendPort 8010 -FrontendPort 5180`. See the [startup guide](backend/docs/RUNNING.md).

For manual startup:

Use two PowerShell terminals. These commands assume the repository is located at
`D:\python-api`; adjust the path if needed. Dependency installation is needed on
first setup or after dependency updates. Existing `.env` files are preserved.

Start the backend:

```powershell
Set-Location D:\python-api\backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv sync --locked
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```powershell
Set-Location D:\python-api\frontend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm ci
npm run dev
```

Local defaults use `http://127.0.0.1:5173` for the website and
`http://127.0.0.1:8000` for the API. For local HTTP only, set
`SESSION_COOKIE_SECURE=false` in `backend/.env`.

Open `http://127.0.0.1:5173/bulk-reg` for independent CSV/XLSX file intake with
drag-and-drop, file browsing, backend-local paths, and a preview. Path loading
requires `ALLOW_LOCAL_FILE_PATHS=true` in `backend/.env`. This page does not use
mapping state or submit registrations, and needs no additional server.

## Deploy on separate domains

Build the frontend with its public API origin:

```env
# frontend/.env.production
VITE_PRODUCTION_API_BASE_URL=https://api.example.com
VITE_API_PREFIX=/api/v1
```

Configure the backend with the exact frontend origin:

```env
# backend/.env
CORS_ORIGINS=https://app.example.com
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=lax
```

The frontend sends API requests with credentials. The backend therefore uses
explicit credentialed CORS and does not permit `CORS_ORIGINS=*`.

Using `app.example.com` and `api.example.com` is recommended. They are separate
origins but the same site, allowing the default `SameSite=lax` cookie policy. If
the two deployments use unrelated sites, set `SESSION_COOKIE_SAMESITE=none` and
keep HTTPS enabled; browser third-party-cookie policies can still prevent such a
session.

Deploy `frontend/dist/` to the frontend host and run the backend from its own
folder with:

```text
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port <PORT>
```

The frontend host must rewrite client-side routes to `index.html`. The backend
deployment must persist `backend/storage/` so active workflows survive restarts.

## Workflow

1. Upload the school file.
2. Upload a student dump or fetch it from SQL using a school index.
3. Run admission mapping.
4. Optionally run email and full-name/class mapping.
5. Preview or download individual result groups.
6. Use **Download mapping results** in the sidebar to export every available group
   as a separate worksheet.

The final workbook is named
`automation-<school-index>-<school-name>.xlsx`. Admission adds three sheets,
Email adds two sheets, and Full Name + Class adds three sheets. Different matched
schemas are kept separate.

## Verification

```powershell
Set-Location D:\python-api\backend
uv run python -m unittest discover -s tests -p "test_*.py"

Set-Location D:\python-api\frontend
npm test
npm run build
```

See the [documentation index](backend/docs/README.md),
[backend setup](backend/README.md), [frontend setup](frontend/README.md),
[mapping workflow](backend/docs/MAPPING_WORKFLOW.md), and
[session/data flow](backend/docs/SESSION_AND_DATA_FLOW.md).
