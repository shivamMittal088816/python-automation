# Clone, run, test, and deploy

Current startup commands for the updated folders: [Run the project](RUNNING.md).

## Repository layout

```text
python-api/
├── frontend/       # independent React/Vite deployment
└── backend/        # independent FastAPI deployment
    ├── app/
    ├── tests/
    ├── docs/
    ├── pyproject.toml
    └── uv.lock
```

Use Python 3.12 and Node.js 22.12 or newer.

The PowerShell examples use `D:\python-api` as the checkout location. Replace that
absolute path if needed. If already cloned, skip `git clone`. Dependency setup is
needed initially or after dependency updates; everyday startup only requires the
two service commands in the [startup guide](RUNNING.md).

## Backend setup

```powershell
git clone <repository-url> D:\python-api
Set-Location D:\python-api\backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv sync --locked
```

Fill in the five `DB_*` values in `backend/.env`. For local HTTP development,
also set:

```env
CORS_ORIGINS=http://127.0.0.1:5173
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=lax
```

Start the API from `backend/`:

```powershell
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the API schema.

## Frontend setup

In another terminal:

```powershell
Set-Location D:\python-api\frontend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm ci
npm run dev
```

Open `http://127.0.0.1:5173` for mapping or `http://127.0.0.1:5173/bulk-reg`
for the separate file-intake service. Keep both service terminals running.

The local frontend environment should contain:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_API_PREFIX=/api/v1
```

Do not mix `localhost` and `127.0.0.1`; cookie and origin behavior depends on the
hostname.

## Production deployment

Deploy the two folders independently.

Frontend build variables:

```env
VITE_PRODUCTION_API_BASE_URL=https://api.example.com
VITE_API_PREFIX=/api/v1
```

Build with `npm run build` and publish `frontend/dist/`. Configure the frontend
host to rewrite unknown routes to `index.html`.

Backend variables:

```env
CORS_ORIGINS=https://app.example.com
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=lax
ALLOW_LOCAL_FILE_PATHS=false
MAX_UPLOAD_BYTES=104857600
```

Start the backend from `backend/`:

```text
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port <PORT>
```

Use exact comma-separated origins in `CORS_ORIGINS`; wildcard origins are rejected
because the frontend sends cookies. Subdomains of the same registrable domain are
recommended. For unrelated frontend and API sites, use
`SESSION_COOKIE_SAMESITE=none` with HTTPS, subject to browser third-party-cookie
restrictions.

Persist `backend/storage/` and keep a single application worker until workspace
locking is moved to a distributed lock.

## Verification

Backend:

```powershell
Set-Location D:\python-api\backend
uv run python -m unittest discover -s tests -p "test_*.py"
```

Frontend:

```powershell
Set-Location D:\python-api\frontend
npm test
npm run build
```

Browser tests start an isolated fixture API and do not use production SQL data.

## Common problems

| Problem | Resolution |
|---|---|
| `uv trampoline failed to canonicalize script path` | From `backend/`, use `uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` to bypass the launcher left over from the folder move. |
| CORS error | Add the exact frontend scheme, hostname, and port to backend `CORS_ORIGINS`, then restart the API. |
| Session cookie is missing | Use HTTPS in production; verify `SESSION_COOKIE_SECURE` and `SESSION_COOKIE_SAMESITE`. |
| API cannot be reached | Verify `VITE_PRODUCTION_API_BASE_URL`, rebuild the frontend, and check the backend health route. |
| Client route returns 404 | Configure the frontend host's SPA fallback to `index.html`. |
| Local path loading fails | The path is resolved on the backend host and requires `ALLOW_LOCAL_FILE_PATHS=true`. |
