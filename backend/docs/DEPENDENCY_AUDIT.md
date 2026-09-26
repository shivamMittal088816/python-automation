# Dependency modernization audit — 2026-09-18

Upgraded the project's dependencies while preserving the application. All direct
Python dependencies and all direct frontend dependencies except React Router are
at the latest stable releases returned by PyPI/npm on the audit date. React Router
is at the newest stable release compatible with the existing Node runtime.

No application source or existing tests were modified. The complete OpenAPI
document, compiled MySQL ORM schema, and hashes of 114 backend, frontend source,
and test/fixture files match the baseline. Python remains 3.12.12 with the existing
`>=3.12,<3.13` project constraint; Node remains 22.14.0. npm 11.3.0 and uv 0.11.9
were used. No prerelease packages remain in either lockfile.

## Direct frontend dependencies

“Before” means the installed/locked version, not the older minimum in the manifest.
Several packages were already current; their declared minimums were updated to
the versions actually verified. All after-versions equal registry `latest` except
React Router, whose latest is 8.4.0.

| Package | Previous declaration | Before | After declaration / installed | Installed change |
| --- | --- | --- | --- | --- |
| react | ^19.2.0 | 19.3.0 | ^19.3.0 / 19.3.0 | None |
| react-dom | ^19.2.0 | 19.3.0 | ^19.3.0 / 19.3.0 | None |
| react-router | ^7.13.0 | 7.18.4 | ^7.18.4 / 7.18.4 | None; runtime exception below |
| @playwright/test | ^1.58.0 | 1.63.0 | ^1.63.0 / 1.63.0 | None |
| @tailwindcss/vite | ^4.2.0 | 4.3.3 | ^4.3.3 / 4.3.3 | None |
| @vitejs/plugin-react | ^5.1.0 | 5.2.0 | ^6.1.1 / 6.1.1 | **Major** |
| nodemon | ^3.1.14 | 3.1.14 | ^3.1.14 / 3.1.14 | None |
| tailwindcss | ^4.2.0 | 4.3.3 | ^4.3.3 / 4.3.3 | None |
| vite | ^7.3.0 | 7.3.6 | ^8.3.0 / 8.3.0 | **Major** |

No separate ESLint, PostCSS, Axios, icon library, unit-test runner, or
react-router-dom dependency was declared. Existing Playwright tests are the
frontend test suite. Tailwind uses its existing Vite plugin and CSS import;
there was no Tailwind major migration or styling architecture change.

## Direct Python dependencies

Each previous declaration was `>=Before`, and each new declaration is `>=After`.
All after-versions below are the latest stable, non-yanked PyPI releases verified
during the audit. Their Python requirements all permit the existing Python 3.12.

| Package | Before | After | Installed change | Latest requires Python |
| --- | --- | --- | --- | --- |
| fastapi | 0.136.1 | 0.141.1 | Minor; breaking internals reviewed | >=3.10 |
| loguru | 0.7.3 | 0.7.3 | None | >=3.5,<4.0 |
| openpyxl | 3.1.5 | 3.1.5 | None | >=3.8 |
| pandas | 3.0.2 | 3.0.6 | Patch | >=3.11 |
| pydantic-settings | 2.14.1 | 2.15.0 | Minor | >=3.10 |
| pymysql | 1.1.3 | 1.2.3 | Minor; breaking defaults reviewed | >=3.9 |
| python-multipart | 0.0.27 | 0.0.32 | Patch in a 0.0 release series | >=3.10 |
| sqlalchemy | 2.0.49 | 2.0.54 | Patch | >=3.7 |
| uvicorn | 0.46.0 | 0.53.0 | Minor; transport changes reviewed | >=3.10 |
| httptools | 0.7.1 | 0.8.0 | Minor | >=3.9 |
| websockets | 16.0 | 17.1 | **Major** | >=3.11 |

Pydantic is transitive, not declared directly. It advanced from 2.13.4 to 2.13.5;
Starlette from 1.0.0 to 1.6.0; NumPy from 2.4.4 to 2.5.3. Other refreshed
transitives are recorded in the generated lockfile and saved package snapshots.
The backend tests use the standard-library unittest runner, so no test dependency
was added.

## Migration assessment and minimal changes

| Area | Relevant upstream change and project assessment | Compatibility action |
| --- | --- | --- |
| Vite 8 | Uses Rolldown/Oxc and changes the default JavaScript browser target and CSS minifier. This project has no custom Rollup/esbuild options or plugins needing migration. | Added `build.target: ['chrome107', 'edge107', 'firefox104', 'safari16']` to preserve Vite 7's JavaScript targets. Verified both development and production browser workflows. |
| React plugin 6 | Requires Vite 8 and removes Babel configuration features. The project uses plain `react()` with no Babel/compiler customization. | Upgraded alongside Vite; no component or plugin configuration rewrite. Experimental React Compiler support remains disabled. |
| FastAPI | 0.137 changes `router.routes` internals from a flat list to a router tree. This project uses supported router registration and does not traverse those internals. | No source changes; full schema equality and API tests pass. |
| Uvicorn / websockets | websockets 17 removes deprecated aliases, changes some positional arguments and handshake behavior, and requires Python >=3.11. Uvicorn >=0.50 selects the supported Sans-I/O WebSocket transport by default. | Upgraded Uvicorn, httptools, and websockets together. Transport initialization, real HTTP startup and tests pass. No application WebSocket routes or direct websockets API calls exist. Experimental HTTP parsers/HTTP2 were not enabled. |
| PyMySQL / SQLAlchemy | PyMySQL 1.2 changes ping reconnection/TLS defaults and tightens byte-parameter escaping. SQLAlchemy's dialect handles ping compatibility; application repositories pass string/numeric parameters and do not use removed cursor APIs. | Kept engine, SQL, session configuration and models unchanged. Unit/API tests pass. Actual MySQL connectivity was unavailable before and after, limiting live integration verification. |
| pandas / openpyxl | pandas is a 3.0 patch update; openpyxl was already latest. | No algorithm or serialization changes. Existing identifier, duplicate, CSV/XLSX, workbook, and all three mapping-stage tests pass. |
| Stable resolution | Future uv resolution should follow the requested stable-only policy. | Added `[tool.uv] prerelease = "disallow"`; runtime constraints are unchanged. |

Official sources reviewed: [Vite 8 migration](https://vite.dev/guide/migration),
[React plugin changelog](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/CHANGELOG.md),
[React Router migration](https://reactrouter.com/upgrading/v7),
[FastAPI release notes](https://fastapi.tiangolo.com/release-notes/#01370),
[Uvicorn release notes](https://github.com/Kludex/uvicorn/blob/main/docs/release-notes.md),
[websockets changelog](https://websockets.readthedocs.io/en/stable/project/changelog.html),
[PyMySQL changelog](https://github.com/PyMySQL/PyMySQL/blob/main/CHANGELOG.md),
[SQLAlchemy changelog](https://docs.sqlalchemy.org/en/20/changelog/changelog_20.html),
[pandas release](https://github.com/pandas-dev/pandas/releases/tag/v3.0.6), and
[Pydantic settings release](https://github.com/pydantic/pydantic-settings/releases/tag/v2.15.0).
Version selection used live npm/PyPI metadata, not documentation version guesses.

## Packages intentionally below registry latest

| Dependency | Before | Latest stable | Newest safely compatible used | Reason and required migration |
| --- | --- | --- | --- | --- |
| react-router (direct) | 7.18.4 | 8.4.0 | 7.18.4 | Router 8 requires Node >=22.22; installed Node is 22.14 and the project supports >=22.12. Kept the current runtime and latest v7. Adopting v8 requires updating the Node deployment/development baseline and engine declaration, reviewing the v8 migration, and rerunning navigation/workflow tests. |
| pydantic-core (transitive) | 2.46.4 | 2.49.0 | 2.46.5 | Latest stable Pydantic 2.13.5 explicitly requires `pydantic-core==2.46.5`. A newer core cannot be installed compatibly by itself. Wait for a compatible stable Pydantic release and upgrade the pair. |

All other installed Python packages are current according to the final uv
outdated query. `npm outdated --include=dev --json` returned `{}` on this Node
runtime. That result alone does not establish Router is globally latest:
`npm view react-router@latest` explicitly returned 8.4.0 and the newer Node engine
requirement. Both sources were checked.

## Verification

| Check | Before | After |
| --- | --- | --- |
| Backend full unittest suite | **59 passed** | **59 passed** after each backend group and final transitive refresh |
| Standard `npm test` / Playwright / Edge | **6 passed** | **6 passed**, including final combined dependency set |
| Same Playwright suite against production bundle | Not a separate baseline run | **6 passed** |
| `npm run build` | Passed, Vite 7.3.6 | Passed, Vite 8.3.0; final dist rebuilt with normal API configuration |
| Vite development startup | Passed through E2E web server | Passed through final `npm test` |
| Actual FastAPI import and startup | Passed | Passed |
| Real health and OpenAPI HTTP endpoints | Both HTTP 200 | Both HTTP 200 |
| Complete generated OpenAPI schema | Saved | Exactly unchanged |
| Compiled MySQL ORM schema | Saved | Exactly unchanged |
| Application source and existing test/fixture hashes | 114 files saved | All 114 unchanged |
| Real database startup `SELECT 1` | Connection unavailable; app starts in existing file-workflow mode | Same limitation; no schema/data changes performed |
| npm audit, including development packages | 0 vulnerabilities | **0 vulnerabilities** |
| Python advisory audit | Not run separately | **0 known vulnerabilities** across 31 locked installed packages |
| Python dependency consistency | Installed versions recorded | `uv pip check`: all compatible |
| Lockfile consistency | Baseline saved | `uv lock --check` passes; npm installation/update and builds pass |
| ESLint | Not configured | Not configured; no rules disabled or tooling introduced |

The initial sandbox-only attempts produced filesystem permission errors and
`spawn EPERM`. Rerunning the unchanged baseline with the required process/temp-file
access passed. These were environment restrictions, not baseline application
failures. No failing tests were deleted, skipped or weakened.

Existing tests cover admission/email/full-name-class mapping, Matched/Review students/Not
matched handoffs, duplicate/account uniqueness, identifiers, CSV/XLSX uploads and
exports, search, pagination, file and dump browsing, route navigation, explicit
start behavior, workspace persistence/restoration, validation, CORS and error
responses. Database repositories are fixture-backed in browser tests; those tests
do not establish live MySQL connectivity.

Visual checks used all seven active pages at 1440, 820 and 390 pixel widths,
plus empty, configured, result, loading and error states. Immediately after the
Vite migration, 28 of 30 screenshots were byte-identical to baseline. Two differed
because of a loading state and spinner phase. Final combined runs also expose
asynchronous result-loading timing in the existing screenshot test. Production
screenshots have a few 2–8 pixel rasterization differences from CSS minification,
plus the same loading-state timing. Inspected differences show no layout, color,
typography or workflow redesign; UI appearance was intentionally preserved.

## Files and lockfiles

- `frontend/package.json`: updated dependency minimums and the two build-tool majors.
- `frontend/package-lock.json`: regenerated by `npm install --include=dev` and
  `npm update --include=dev`; transitive packages refreshed, obsolete build packages
  removed, and the old plugin-utils prerelease replaced by a stable release.
- `frontend/vite.config.js`: one compatibility setting preserving JavaScript targets.
- `pyproject.toml`: updated nine dependency minimums and disallowed prerelease resolution.
- `uv.lock`: regenerated by staged `uv lock --upgrade-package ...`, then
  `uv lock --upgrade`; synchronized with `uv sync --frozen --link-mode copy`.
- `docs/DEPENDENCY_AUDIT.md`: this report.

Neither lockfile was edited manually. No frontend or backend application source,
test, route, schema definition, SQL, mapping algorithm, environment-variable name,
request/response field, or database migration was changed. README and existing
docs had no dependency version references made outdated by these upgrades, so
they were left intact. Temporary production-test configuration was removed.

## Remaining warnings and operational notes

- Existing `backend/app/config/settings.py` uses class-based Pydantic `Config`.
  Pydantic warns that this will be removed in v3. It remains supported in the
  installed v2, so this modernization did not rewrite settings behavior.
- Playwright subprocesses report that `FORCE_COLOR` overrides `NO_COLOR` in the
  host environment. This occurred before and after; it does not affect tests.
- Windows initially blocked replacing the loaded httptools extension. The existing
  development server was briefly stopped, the package reinstalled with uv, and
  obsolete incomplete metadata moved to the audit artifacts. Final `uv pip check`
  passes with one installed httptools distribution.
- The development server was restarted with its original
  `-m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` arguments.
  Its output is under `logs/dependency-upgrade-server.*.log`.
- uv's cache is on C: and the project is on D:, so subsequent syncs used
  `--link-mode copy` after uv's harmless cross-filesystem hardlink fallback warning.
- The isolated Python security tool warned about unhashed audit input and normalized
  old metadata while resolving its own environment. Project installation still uses
  the hashed uv lockfile; the audit did not replace uv or add project dependencies.

Saved registry metadata, baseline/final package inventories, schema/source
snapshots, backend test output, startup logs, security results and screenshots are
under `logs/dependency-audit-2026-09-18/` (already ignored by the repository).
No known security findings remain. Live MySQL integration remains unverified
because connectivity was unavailable in both baseline and final checks.
