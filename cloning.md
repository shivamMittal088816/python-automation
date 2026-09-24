# Clone and run Student Mapping

This guide explains how to run the current React + FastAPI application on a new
computer. Streamlit is not required.

The application compares school student records with existing student accounts,
classifies results as **Matched**, **Review students**, or **Not matched**, and exports CSV
or Excel files. You run two processes: the Python API and the React frontend.

## Contents

1. [Before cloning](#1-before-cloning)
2. [Install the prerequisites](#2-install-the-prerequisites)
3. [Clone the repository](#3-clone-the-repository)
4. [Install Python dependencies](#4-install-python-dependencies)
5. [Configure the backend](#5-configure-the-backend)
6. [Install and configure the frontend](#6-install-and-configure-the-frontend)
7. [Start the application](#7-start-the-application)
8. [Try the sample files](#8-try-the-sample-files)
9. [Use your own files and database](#9-use-your-own-files-and-database)
10. [Understand saved files](#10-understand-saved-files)
11. [Run tests](#11-run-tests)
12. [Build the frontend](#12-build-the-frontend)
13. [Troubleshooting](#13-troubleshooting)
14. [Start again or update later](#14-start-again-or-update-later)
15. [macOS and Linux commands](#15-macos-and-linux-commands)

## 1. Before cloning

**For the repository maintainer:** this folder has been disconnected from the old
Git repository. Publish the reviewed source as a new repository, including the
frontend, backend, lockfiles, safe configuration examples, tests, and this guide.
Replace `YOUR_NEW_REPOSITORY_URL` below with the new GitHub clone URL before sharing.

The root `.gitignore` excludes real environments, runtime data, logs, and generated
files. Keep synthetic fixtures and `.env.example` templates. Removing the old local
Git history does not revoke credentials or data previously published elsewhere;
see [GITHUB_SAFETY.md](docs/GITHUB_SAFETY.md).

**For someone cloning:** obtain access to the repository and the branch containing
the current implementation. After cloning, check that these files exist:

```text
python-api/
|-- frontend/                 # React/Vite frontend, package.json, e2e tests
|-- Backend/                 # FastAPI backend
|   |-- main.py
|   |-- scripts/            # Python CLI and administration tools
|   `-- tests/              # Python tests and browser fixture API
|-- docs/                   # Supporting documentation
|-- pyproject.toml
|-- uv.lock
|-- .env.example
`-- cloning.md
```

If `frontend/` or `Backend/` is missing, obtain the updated branch from the maintainer
before continuing. Old Streamlit startup instructions do not apply to this version.

## 2. Install the prerequisites

The main instructions use **Windows PowerShell**. There are equivalent application
startup commands for macOS/Linux at the end.

| Requirement | What you need |
| --- | --- |
| Git | Installed and available in your terminal. |
| Python | **3.12**. The project requires `>=3.12,<3.13`. |
| uv | Installs the Python environment from `uv.lock`. |
| Node.js | **22.12 or newer**, as declared in `frontend/package.json`. |
| npm | Installed with Node.js; installs frontend dependencies. |
| Browser | A browser to use the UI. Microsoft Edge is the default for automated tests. |
| MySQL access | Required for database dump fetching and email lookup; optional for the uploaded-file example. |

Install Git, Python 3.12, and a compatible Node.js version using your organization's
normal installation method. Open a new terminal after installing them.

Check the tools:

```powershell
git --version
py -3.12 --version
node --version
npm.cmd --version
```

If uv is not already installed, install it using Python:

```powershell
py -3.12 -m pip install uv
```

This guide invokes uv as a Python module so it also works when the `uv` executable
is not on `PATH`. An existing `uv` installation can use `uv sync --frozen` instead.

## 3. Clone the repository

Open PowerShell in the parent folder where you want to keep the project:

```powershell
git clone YOUR_NEW_REPOSITORY_URL python-api
cd python-api
```

The explicit `python-api` argument gives the local folder a simple name. Its full
path does not have to be `D:\python-api`.

If the current implementation is on another branch, replace the placeholder below
with the branch name provided by the maintainer:

```powershell
git switch YOUR_BRANCH_NAME
```

If Git requests authentication, use your own authorized GitHub access. Cloning the
source does not provide database credentials or access to private student data.

## 4. Install Python dependencies

Run from the **repository root**, the folder containing `pyproject.toml`:

```powershell
py -3.12 -m uv sync --frozen
.\.venv\Scripts\python.exe --version
```

This creates `.venv/` and installs the locked Python dependencies, including
FastAPI, Uvicorn, pandas, openpyxl, SQLAlchemy, and PyMySQL. Do not copy another
computer's `.venv` folder.

The remaining commands use the environment's Python executable directly, so
activating the environment is unnecessary and PowerShell activation policy does
not block setup.

## 5. Configure the backend

Copy the safe backend template from the repository root (do not overwrite an
already configured `.env`):

```powershell
Copy-Item .env.example .env
```

Edit **`.env` in the repository root**. Make sure the filename is not `.env.txt`.
Its configuration includes:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name

API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ALLOW_LOCAL_FILE_PATHS=true
```

Replace the five `DB_*` values with the values supplied by your database
administrator when using real SQL data. A VPN or network allowlist may also be
required for your organization's database.

**All five database settings must be present even for uploaded-file workflows.**
They are validated when the API starts. For the sample upload exercise, the
placeholder values above are sufficient: admission mapping against an uploaded
dump does not need a live database connection. Database fetching, student listing,
and normal email mapping require the actual database.

| Optional setting | Default | Meaning |
| --- | --- | --- |
| `APP_NAME` | `Student Mapping API` | Title displayed by FastAPI. |
| `API_V1_PREFIX` | `/api/v1` | API URL prefix; keep the frontend prefix consistent. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Browser origins allowed to call the API. |
| `ALLOW_LOCAL_FILE_PATHS` | `true` | Allows loading a path on the backend computer. |

Run the backend from the root so it can read this `.env`. Restart the backend
after editing its settings. Database credentials belong in this backend file,
never in frontend environment variables.

## 6. Install and configure the frontend

From the repository root:

```powershell
cd frontend
npm.cmd ci
```

`npm ci` installs the exact dependencies from `package-lock.json`. A missing
lockfile means the checkout is incomplete; obtain it from the maintainer.

For a new checkout, copy the frontend configuration example:

```powershell
Copy-Item .env.example .env
```

If `frontend/.env` already exists, inspect it instead of overwriting your settings.
Its local defaults should be:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_API_PREFIX=/api/v1
```

The base URL is the address of FastAPI; do not append `/api/v1` to it because the
prefix is configured separately. Frontend environment values are visible to the
browser. Restart Vite after changing them; rebuild for a production build.

Return to the root:

```powershell
cd ..
```

## 7. Start the application

Keep **two terminals** open.

### Terminal 1: backend

Open the repository root and run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn Backend.main:app --reload --reload-dir Backend --host 127.0.0.1 --port 8000
```

Wait for `Application startup complete`. This terminal must stay running.

### Terminal 2: frontend

Open a second terminal in the repository root:

```powershell
cd frontend
npm.cmd run dev
```

Use `npm run dev` for development: nodemon launches `npm run start` and restarts
Vite when its configuration or frontend environment files change. React/CSS source
changes update the browser through Vite's hot module replacement without requiring
a manual refresh in normal use.

Alternatively, `npm run start` starts Vite directly. Both commands run the frontend
only; keep the backend terminal running. On PowerShell, `npm.cmd` is equivalent
and avoids execution-policy issues with `npm.ps1`.

Wait for Vite to print its local URL. Open **http://127.0.0.1:5173**.

| Address | Purpose |
| --- | --- |
| http://127.0.0.1:5173 | The React application you use. |
| http://127.0.0.1:8000/docs | Interactive API documentation. |
| http://127.0.0.1:8000/api/v1/mapping/health | API health check. |

The API root at `http://127.0.0.1:8000/` is not the React UI. A 404 at that root
does not mean the API failed. The health endpoint verifies API availability, not
the database connection.

You can check health from another PowerShell terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/mapping/health
```

## 8. Try the sample files

This exercise needs no real student data or live MySQL connection. Keep the
backend `.env` configured as described above.

1. Open **Admission mapping**.
2. In **School file**, choose `frontend/e2e/fixtures/school.csv`.
3. In **Student dump**, choose **Upload dump file**, then select
   `frontend/e2e/fixtures/dump.csv`.
4. Select `admission_number` as the school admission number column and
   `first_name` as the first-name column.
5. Click **Start admission mapping**. File selection alone does not run mapping.
6. Open a result Preview screen and try **Download Excel** or **Download CSV**.

With these fixtures, admission mapping produces **1 Matched, 0 Review students, and
3 Not matched** records after dropping one identical duplicate school row.

To try the final mapping stage without MySQL, open **Full name + class Number**,
choose **Admission mapping — Not matched**, select `full_name` and `classNumber`,
and click **1st round mapping**. The fixture dump includes `generated_col`.
If records remain Not matched, choose the dump full-name and class columns and
click **2nd round mapping** to compare sorted name characters and class numbers.
Selecting `user_edu_class` adds 1 to its stored number for this second round.

Normal **Email mapping** fetches student records from MySQL. It will not work with
placeholder credentials; the automated browser tests use fixture database responses
to exercise that stage without a live database.

## 9. Use your own files and database

### Uploaded-file workflow

- Use CSV or XLSX school files and dump files.
- For Excel files, choose the intended worksheet.
- Keep identifiers such as admission numbers and user IDs as text in your source
  files when leading zeros matter.
- The application validates dump columns and tells you which required columns
  are missing. The sample dump provides a working example of column names.
- Full-name/class mapping needs the dump's `generated_col` column.
- A **File path** refers to the machine running FastAPI, not necessarily the
  browser's computer. Use upload when the file is only on your own computer.

### Database workflow

The SQL integration expects an **existing compatible database**. Creating a blank
MySQL database is not enough. Obtain the schema/data and access details from your
team.

The school dump queries use `users_schools`, `users`, and `paid_users`; email lookup
queries `users`. Exact selected columns and joins are defined in:

- [Admission database queries](Backend/repositories/admission_dump_service.py)
- [Email database queries](Backend/repositories/email_dump_service.py)

In Admission mapping, choose **Fetch from SQL**, enter a valid school index, and
click **Fetch dump data**. The query selects school users with `user_type = '0'`
and attaches admissions using `LEFT JOIN paid_users` by `user_id`. Students without
paid records stay in the dump with blank admissions. Multiple distinct admissions
can still produce multiple rows for one student; no first/latest record is selected.
See [SQL dump selection and counts](docs/MAPPING_WORKFLOW.md#sql-dump-selection-and-counts).
SQL `NULL` cells are normalized to empty text and rows
that then become completely identical are retained once. A failed fetch preserves
the previously loaded dump and results. Once files and columns are ready, click **Start admission
mapping**. For remaining students, select their email and first-name columns and
run Email Pass 1. It compares email plus first name, and sends matching
one-character first names to Review. Email Pass 2 uses a separately selected full
name and sorted full-name characters. Then optionally use
**1st round mapping** and **2nd round mapping** for full-name/class matching.

Do not run `Backend/scripts/init_db.py` as a general setup step. It creates the ORM
`students` table and performs database writes; it does not create or populate the
external `users`, `paid_users`, or `users_schools` schema needed by dump fetching.

Mapping results are saved as files; the file-mapping workflow does not write its
classifications back into SQL. Result Preview screens are locked against manual moves
between groups. Jobs and standalone Review students pages are not part of this version.

## 10. Understand saved files

| Location | Contents |
| --- | --- |
| `storage/temp/workflow_sessions/` | Session manifests, input snapshots, and results. |
| `storage/admission_mapping/` | Saved workspaces for identified schools. |
| `logs/` | Any runtime log files captured/configured for this checkout. |
| `frontend/dist/` | Generated frontend build, created by `npm run build`. |

Storage directories are created as needed. The backend user needs write access
to the project storage directory. A fresh clone does not need another user's saved
workspace or historical logs.

The browser stores a session identifier; the backend stores the actual files.
School index/name metadata supports saving and restoring a school workspace.
Keep the relevant storage when restarting if you want to preserve work.

Opening a mapping page can show **Saved mapping results** from an earlier run.
This does not mean a new mapping operation started automatically.

Logs normally appear in the terminals used above. These commands do not
automatically redirect terminal output into `logs/`.

## 11. Run tests

### Python tests

From the repository root, with dependencies and backend configuration in place:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s Backend/tests -v
```

### Frontend/browser tests on Windows

Install frontend dependencies first. The current Playwright configuration uses
**Microsoft Edge** and Windows Python executable paths.

Stop the normal frontend with `Ctrl+C` so port 5173 is free. From `frontend/`:

```powershell
npm.cmd test
```

Tests start an isolated fixture API on port 8123 and their own Vite Backend. They
exercise actual application services with fixture repositories and temporary
storage; they do not need your real SQL data. Backend settings must still exist.

If you want to leave the normal frontend running on 5173, use the existing
alternate configuration:

```powershell
npm.cmd test -- --config=playwright.feature-removal.config.js
```

That uses frontend port **5174** and API port **8123**. Both must be free. Despite
its filename, it runs the current test suite, including the UI checks.

The suite covers mapping start actions, uploads, file paths, dump fetching,
downloads, search, reload restoration, and responsive layouts. Generated screenshots
and failure traces are written under `frontend/test-results/`.

## 12. Build the frontend

From `frontend/`:

```powershell
npm.cmd run build
```

The compiled site is written to `frontend/dist/`. FastAPI remains a separate process;
building React does not start the API or configure hosting.

To inspect the build locally, first add Vite build-server origins to the **root** `.env`:

```dotenv
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173
```

Restart FastAPI, then run from `frontend/`:

```powershell
npm.cmd run preview
```

Open the URL Vite prints, normally http://127.0.0.1:4173. The Vite `preview` command is a local build
check, not a production deployment configuration. A deployed frontend also needs
SPA fallback to `index.html` for React routes and an API URL reachable by its users.

## 13. Troubleshooting

| Problem | Check or fix |
| --- | --- |
| `git`, `node`, or `py` is not recognized | Install the prerequisite and reopen the terminal. Check Python 3.12 specifically. |
| `npm.ps1 cannot be loaded` | Use `npm.cmd` as shown; no activation or execution-policy change is needed. |
| uv rejects the Python version | Use Python 3.12. Python 3.13 is outside this project's declared range. |
| uv says the lockfile is incompatible/outdated | Obtain matching `pyproject.toml` and `uv.lock` from the same branch; do not regenerate a shared lockfile just to bypass setup. |
| `DB_HOST` or another setting is missing | Create root `.env`, include all five `DB_*` values, and start the API from the root. |
| `No module named server` | Run the backend command from the repository root and confirm `Backend/` exists. |
| `Could not reach the API` | Check the backend terminal, health endpoint, `frontend/.env`, and port 8000. Restart Vite after changing its environment. |
| A CORS error appears in the browser | Add the exact frontend origin, including its port, to root `CORS_ORIGINS`; restart FastAPI. |
| MySQL access denied / connection refused | Check credentials, host, port, network/VPN access, and database permissions. API health alone does not validate SQL. |
| Connection fails with punctuation in a password | The current backend interpolates credentials into a SQLAlchemy URL. Reserved URL characters may require percent-encoding in the configured credential; ask the maintainer if unsure. |
| A SQL table/column is missing | The integration expects your team's existing schema. `init_db.py` does not provision that schema. |
| School index cannot be found | Confirm it exists in `users_schools` in the configured database. |
| Email mapping fails with sample credentials | Normal email lookup requires MySQL. Use the uploaded-file exercise or automated fixture tests. |
| Vite says port 5173 is in use | Stop the old frontend terminal, or choose another port and update backend CORS accordingly. Vite uses strict port checking. |
| Backend port 8000 is in use | Stop the old backend or use another port and update `VITE_API_BASE_URL`. |
| A local file path cannot be loaded | Check the path on the backend computer, its read permissions, and `ALLOW_LOCAL_FILE_PATHS`. |
| Playwright cannot find Edge | Install Microsoft Edge for the provided default configuration. |
| Browser tests cannot start a server | Ensure test ports are free; the configs intentionally do not reuse existing servers. |
| Tests fail on Linux/macOS before launching Python | The checked-in browser-test configs use Windows executable paths; see the platform note below. |

## 14. Start again or update later

To stop the application, press **Ctrl+C in both server terminals**. No uninstall
is needed, and dependencies do not need reinstalling for each run.

For the next session, repeat only the two commands in [Start the application](#7-start-the-application).

To update from the repository, save your local work first. From the root:

```powershell
git pull
py -3.12 -m uv sync --frozen
cd frontend
npm.cmd ci
```

Restart both processes after updating. Keep your own environment configuration and
check for any new setup requirements in the updated documentation.

## 15. macOS and Linux commands

The application source can be run with the equivalent Unix environment paths.
These commands are provided as platform equivalents; verification in this workspace
was performed on Windows.

With Git, Python 3.12, compatible Node/npm, and uv installed:

```bash
git clone YOUR_NEW_REPOSITORY_URL python-api
cd python-api
uv sync --frozen
```

Create root `.env` with the same backend settings described above. Then:

```bash
cd frontend
npm ci
cp .env.example .env
cd ..
```

Terminal 1, from the root:

```bash
.venv/bin/python -m uvicorn Backend.main:app --reload --reload-dir Backend --host 127.0.0.1 --port 8000
```

Terminal 2, from the root:

```bash
cd frontend
npm run dev
```

Python tests from the root:

```bash
.venv/bin/python -B -m unittest discover -s Backend/tests -v
```

The checked-in **browser-test launcher is Windows-specific**. On macOS/Linux its
Python command must be adapted to `../.venv/bin/python -B ../Backend/tests/browser_fixture_server.py`,
and the configured browser channel must be available. Do not expect the current
`npm test` configuration to work unchanged on those platforms.

For implementation details, see [README.md](README.md) and [CODE_FLOW.md](docs/CODE_FLOW.md).
