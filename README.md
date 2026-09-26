# Student Mapping

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

Start the backend:

```powershell
Set-Location backend
Copy-Item .env.example .env
uv sync --locked
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```powershell
Set-Location frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Local defaults use `http://127.0.0.1:5173` for the website and
`http://127.0.0.1:8000` for the API. For local HTTP only, set
`SESSION_COOKIE_SECURE=false` in `backend/.env`.

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
uv run uvicorn app.main:app --host 0.0.0.0 --port <PORT>
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
Set-Location backend
uv run python -m unittest discover -s tests -p "test_*.py"

Set-Location ..\frontend
npm test
npm run build
```

See [backend setup](backend/README.md), [frontend setup](frontend/README.md),
[mapping workflow](backend/docs/MAPPING_WORKFLOW.md), and
[session/data flow](backend/docs/SESSION_AND_DATA_FLOW.md).
