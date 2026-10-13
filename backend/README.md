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

### Demo: concurrent requests

`GET http://127.0.0.1:8000/debug/concurrency` holds a worker thread for five
seconds and logs START/END counts. It uses the existing app and is intended for
local demos; remove this route before deploying if it is no longer needed.

To send 100 requests concurrently, keep the backend running and execute this
in a second PowerShell terminal from `backend`:

```powershell
@'
import json
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from urllib.request import urlopen

def request(_):
    with urlopen("http://127.0.0.1:8000/debug/concurrency", timeout=120) as response:
        return json.load(response)

started = perf_counter()
with ThreadPoolExecutor(max_workers=100) as pool:
    results = list(pool.map(request, range(100)))
for process_id in sorted({row["process_id"] for row in results}):
    rows = [row for row in results if row["process_id"] == process_id]
    print("Process:", process_id)
    print("Peak active demo requests:", max(row["peak_active_requests"] for row in rows))
    print("Distinct demo threads used:", len({row["thread_id"] for row in rows}))
    print("Maximum sampled live Python threads:", max(row["python_threads_alive"] for row in rows))
print("Elapsed seconds:", round(perf_counter() - started, 2))
'@ | uv run python -
```

`active_when_started` counts only overlapping calls to this endpoint.
`peak_active_requests` records the highest overlap since this app instance
started; restart the backend for a fresh measurement. `python_threads_alive`
is a snapshot of live Python threads in that process, including other work.
Neither value is a project-wide thread maximum. Counters are separate for
each worker process. Send requests concurrently to observe overlap; sequential
requests show one active request. This demo does not change thread-pool limits.

Start the frontend in a second terminal using the [startup guide](docs/RUNNING.md).
The independent bulk registration intake endpoint is `POST /api/v1/bulk-reg/files`.

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

## Backend module boundaries

FastAPI route definitions are under `app/routes`. Shared cookie, workflow-state,
snapshot, validation, and response helpers are under `app/api`. Business operations
live in `app/services`, database access in `app/repositories`, HTTP contracts in
`app/schemas`, and application-owned ORM tables in `app/models`.

Existing platform tables are queried through repositories and are not created by this
service. Their ownership and consumed columns are documented in
`docs/EXTERNAL_DATABASE_SCHEMA.md`.

## Bulk registration backend flow

The bulk router is assembled from the modules in `app/routes/bulk_registration`.
`file_routes.py` handles file intake and input pages, `school_routes.py` validates school
identity, `conversion_routes.py` generates output pages, verification results, and
downloads, and `workspace_routes.py` restores or clears the independent workspace.

Routes call `app/services/bulk_registration.py` for conversion, username/email generation,
verification, and export behavior. Snapshot persistence is isolated in
`bulk_registration_storage.py`; SQL lookups are isolated in `app/repositories`.
