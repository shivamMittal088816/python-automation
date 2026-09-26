# Frontend/backend deployment split

Current startup commands for the updated folders: [Run the project](RUNNING.md).

## Result

The repository now has two deployable application directories:

```text
python-api/
├── frontend/
└── backend/
    ├── app/
    ├── tests/
    ├── docs/
    ├── .env.example
    ├── .python-version
    ├── pyproject.toml
    └── uv.lock
```

Root-level files are limited to repository metadata and the overview README. Local
backend runtime data and the Python virtual environment were moved under
`backend/`; they remain ignored by Git.

## Backend changes

- The former `Backend` package is now `backend/app` and imports use `app.*`.
- Tests live at `backend/tests` and run from the backend directory.
- Python version, dependencies, lockfile, environment template, docs, storage, and
  logs are owned by `backend/`.
- The ASGI entry point is `app.main:app`.
- FastAPI no longer builds or serves the React bundle.
- The backend exposes API and health endpoints only.

## Frontend changes

- React source, browser tests, npm dependencies, environment template, and build
  output remain under `frontend/`.
- Production builds use `VITE_PRODUCTION_API_BASE_URL` to reach the separately
  deployed API.
- Playwright starts the fixture API from `backend/tests/browser_fixture_server.py`.

## Cross-origin session configuration

Frontend requests use `credentials: include`. The backend therefore:

- accepts only explicit comma-separated `CORS_ORIGINS`;
- enables credentialed CORS;
- validates unsafe-request origins;
- uses HTTPS-only cookies in production; and
- exposes `SESSION_COOKIE_SAMESITE` for same-site subdomain or cross-site hosting.

Recommended deployment:

```text
https://app.example.com  -> frontend/dist
https://api.example.com  -> uvicorn app.main:app
```

This is cross-origin but same-site, so the default `SameSite=lax` policy normally
works. Unrelated sites require `SameSite=none`, HTTPS, and browser support for the
resulting third-party cookie.

## Commands

After completing the [dependency and environment setup](RUNNING.md), start each
service in its own PowerShell terminal.

Terminal 1 (backend):

```powershell
Set-Location D:\python-api\backend
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 (frontend):

```powershell
Set-Location D:\python-api\frontend
npm run dev
```

Open `http://127.0.0.1:5173` or `http://127.0.0.1:5173/bulk-reg`.
See [verification commands](RUNNING.md#verification-commands) for tests and builds.

## Verification baseline

- Backend: 144 tests pass.
- Frontend: 18 Playwright tests pass.
- Frontend production build succeeds.
