# Run the project after the folder update

Use two PowerShell terminals. The commands below assume the repository is at
`D:\python-api`; replace that path if you cloned it elsewhere. Python 3.12, uv,
and Node.js 22.12 or newer are required by the project manifests.

## First-time setup or dependency updates

Backend:

```powershell
Set-Location D:\python-api\backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv sync --locked
```

Frontend:

```powershell
Set-Location D:\python-api\frontend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm ci
```

These commands preserve existing environment files. Configure database values in
`backend/.env` for SQL-dependent features. For local HTTP development, use:

```env
CORS_ORIGINS=http://127.0.0.1:5173
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=lax
ALLOW_LOCAL_FILE_PATHS=true
```

In `frontend/.env`, use:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_API_PREFIX=/api/v1
```

## Start both services with the script

After setup, start both services from one terminal:

```powershell
Set-Location D:\python-api
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-project.ps1
```

The script resolves folders relative to itself, bypasses the moved Uvicorn
launcher, verifies that both servers respond, and stores output in root `logs/`.
It sets local HTTP cookie, CORS, and matching `/api/v1` backend/frontend variables for its child
processes without editing `.env`. Keep the terminal open; Ctrl+C stops both
process trees. Existing listeners are not stopped automatically.

To run alongside existing servers:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-project.ps1 -BackendPort 8010 -FrontendPort 5180
```

That example serves the UI on port 5180 and the API on port 8010. For manual
startup on the default ports, use the two terminals below.

## Terminal 1: backend

```powershell
Set-Location D:\python-api\backend
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Terminal 2: frontend

```powershell
Set-Location D:\python-api\frontend
npm run dev
```

Keep both terminals running. Use Ctrl+C in each terminal to stop the services.
Virtual environment activation is unnecessary when using `uv run`.

If an older command reports `uv trampoline failed to canonicalize script path`,
the moved virtual environment can contain a launcher pointing to its previous
location. Use `uv run python -m uvicorn` as shown above to run Uvicorn through
Python instead of that launcher. The installed Python environment does not need
to be deleted for this workaround.

| Page | URL |
|---|---|
| Mapping application | http://127.0.0.1:5173 |
| Bulk registration file intake | http://127.0.0.1:5173/bulk-reg |
| API documentation | http://127.0.0.1:8000/docs |

`/bulk-reg` is a frontend route with separate backend endpoints:
`POST /api/v1/bulk-reg/files` and `POST /api/v1/bulk-reg/files/path`.
It accepts CSV/XLSX uploads or a path on the backend computer. Verify the school
index to fetch its name, generate the fixed 24-column preview, then download CSV or XLSX. School verification requires the database; preview and download use
`POST /api/v1/bulk-reg/convert`. It does not use mapping workspace state or submit
registrations. See [conversion rules](BULK_REGISTRATION.md).
Both services above are sufficient; no third terminal is required.

Use `127.0.0.1` consistently in browser URLs and environment settings. The backend
does not serve the frontend. In deployment, the frontend host must rewrite client
routes, including `/bulk-reg`, to `index.html`.

## Verification commands

Run checks in a separate terminal while development servers are running, or stop
them first. Browser tests launch their own servers on ports 5174 and 8123.

```powershell
Set-Location D:\python-api\backend
uv run python -m unittest discover -s tests -p "test_*.py"

Set-Location D:\python-api\frontend
npm test
npm run build
```

For deployment settings, see [Clone, run, test, and deploy](CLONING.md).
