# Student Mapping Frontend

This folder is a self-contained React/Vite deployment.

## Local setup

```powershell
Set-Location frontend
Copy-Item .env.example .env
npm install
npm run dev
```

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
