# Student Mapping Frontend

Current startup commands for the updated folders: [Run the project](../backend/docs/RUNNING.md).

This folder is a self-contained React/Vite deployment.

## Local setup

Run in a separate PowerShell terminal from the backend. Adjust `D:\python-api`
if your checkout is elsewhere. Dependency installation is needed initially or
after updates; subsequent starts only need `Set-Location` and `npm run dev`.

```powershell
Set-Location D:\python-api\frontend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm ci
npm run dev
```

Use `VITE_API_BASE_URL=http://127.0.0.1:8000` and `VITE_API_PREFIX=/api/v1` in
`frontend/.env`. Start the backend using the [startup guide](../backend/docs/RUNNING.md).

Open `http://127.0.0.1:5173` for mapping, or `http://127.0.0.1:5173/bulk-reg`
for independent CSV/XLSX upload and path loading with a preview. The bulk
registration page does not submit registrations or share mapping state.

## Production configuration

Set the public API origin before building:

```env
VITE_PRODUCTION_API_BASE_URL=https://api.example.com
VITE_API_PREFIX=/api/v1
```

Then build and deploy the generated `dist/` directory:

```powershell
npm run build
```

The API URL is embedded into the browser bundle at build time. After changing it,
build the frontend again. The backend's `CORS_ORIGINS` must contain this frontend's
exact public origin, such as `https://app.example.com`.

The host must route unknown application paths to `index.html` because the project
uses client-side routing.

See the repository [documentation index](../backend/docs/README.md) for the full
workflow, session, and deployment references.
