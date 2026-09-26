# Student Mapping Backend

Current startup commands for the updated folders: [Run the project](docs/RUNNING.md).

This folder is a self-contained FastAPI deployment. It does not build or serve
the React application.

## Local setup

Run in a dedicated PowerShell terminal. Adjust `D:\python-api` if your checkout
is elsewhere; dependency setup is only needed initially or after updates.
Before starting, configure database values in `backend/.env` and set
`SESSION_COOKIE_SECURE=false` for local HTTP. The frontend origin must be included
in `CORS_ORIGINS` (locally `http://127.0.0.1:5173`).

```powershell
Set-Location D:\python-api\backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv sync --locked
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API documentation is available at `http://127.0.0.1:8000/docs`.

Start the frontend in a second terminal using the [startup guide](docs/RUNNING.md).
The independent bulk registration intake endpoints are `POST /api/v1/bulk-reg/files`
and `POST /api/v1/bulk-reg/files/path`. Local paths require
`ALLOW_LOCAL_FILE_PATHS=true` and refer to files on the backend computer.

## Production command

Run the service with the deployment platform's port:

```text
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port <PORT>
```

Set `CORS_ORIGINS` to the exact deployed frontend origin. Multiple origins are
comma-separated; do not use `*` because requests include credentials.

```env
CORS_ORIGINS=https://app.example.com
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=lax
```

`app.example.com` and `api.example.com` are different origins but the same site,
so `SameSite=lax` normally works. If the frontend and API use unrelated sites,
set `SESSION_COOKIE_SAMESITE=none`; HTTPS remains mandatory and browser
third-party-cookie policies may still block the session. Using subdomains of one
registrable domain is recommended.

Persistent deployments must retain `backend/storage/`. Run one application worker
unless the in-process workspace lock is replaced by a distributed lock.

## Tests

```powershell
uv run python -m unittest discover -s tests -p "test_*.py"
```

See the [documentation index](docs/README.md) for architecture, workflow,
deployment, CORS, session, query, and production-readiness references.
