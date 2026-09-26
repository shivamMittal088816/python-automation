# Website test report — 26 September 2026

Current startup commands for the updated folders: [Run the project](RUNNING.md).

Reference: [Session and data flow](SESSION_AND_DATA_FLOW.md).

## Debugging follow-up - 27 September 2026

- Full backend suite: **159 tests passed**. Production frontend build,
  startup-script syntax validation, and `git diff --check` passed.
- Fixed unchanged IndexedDB focus refreshes replacing file objects and closing
  clear-file confirmation dialogs. Cancel and Escape preserve the loaded file.
- Fixed controls remaining disabled after a temporary storage read failure:
  a successful refresh now restores workspace readiness.
- The initial browser run passed 25 of 26 tests. The stale-revision test read the
  session before initialization and sent `undefined`, producing HTTP 422. It now
  waits for both workspaces and asserts a numeric revision before testing HTTP 409.
- After the fixes, all **9 focused browser tests passed**, covering all bulk
  registration tests and the corrected stale-revision test. This includes the
  new storage-recovery regression and confirmation focus/Escape checks.
- Live API verification: `GET /api/v1/bulk-reg/schools/914` returned HTTP 200,
  the requested index, and a nonempty school name. No database writes were made.
- Updated the database query inventory to include bulk registration school lookup.

## Uncommitted-change debugging pass

- Initial full-suite run: **153 backend tests** and **22 browser tests passed**.
- After fixes: **11 focused backend tests** and **6 bulk-registration browser
  tests passed**, including new XLSX, rapid-typing, unavailable BroadcastChannel,
  and blocked-storage regressions. These focused counts overlap the full suite.
- Final production frontend build and `git diff --check` passed.
- Startup script returned HTTP 200 from both services on isolated ports 8017 and
  5187, aligned the API prefix despite a conflicting inherited value, and cleaned
  up both ports when one test service exited. Equal ports are rejected before launch.
- Fixed rapid typing losing characters during asynchronous IndexedDB saves,
  BroadcastChannel initialization failures, failed uploads clearing the previous
  file, repeated row scans during XLSX export, missing bulk-response cache headers,
  and dropped cookie settings in the alternate browser-test configuration.
- Database school lookup was checked with fixtures; this pass does not certify
  connectivity to a live school database. Bulk cross-tab storage is scoped to a
  browser profile and origin, not a signed-in-user or server-session identifier.

## Outcome

- **18 browser tests passed**, using isolated fixture sessions.
- The production frontend build completed successfully.
- **144 backend tests passed**.
- The frontend successfully starts and communicates with the independently
  deployed backend layout.
- No stale UI data was found in the covered browser scenarios. A regression test was
  added for failed/successful SQL dump replacement and result invalidation.

## Coverage

| Area | Verification |
|---|---|
| Session lifecycle | Cookie transport, creation, restoration, reload, reopening a tab and inactivity expiry |
| Concurrency | Shared-session tab refresh plus rejection of a deliberately stale mutation with HTTP 409 |
| Saved school index | SQL fixture fetch restores the saved index after reload; unsubmitted typing does not overwrite it |
| SQL replacement | Failed lookup preserves the loaded dump/results; successful replacement clears stale downstream results |
| Files and storage | CSV/XLSX workflows, upload and local-path loading, saved identifiers, read-only GET behavior, manifest persistence, snapshot garbage collection and source invalidation |
| Admission mapping | Name comparisons, single-character Review checks, duplicates, result Preview screens and downloads |
| Email mapping | Direct school-file input, separate dump, matching rules and downstream invalidation |
| Class concatenation | Direct school-file input, concatenated-key matching, saved results and downloads |
| Metadata caching | Sidebar revisits reuse data, shared admission metadata, source switching, refresh and admission-run invalidation |
| Prerequisites | School or dump changes block both downstream pages until admission mapping runs again |
| Draft selections | Draft edits do not commit mapping settings or run matching; explicit run saves them |
| Preview screen behavior | Source/result API responses, search, paging behavior covered by API tests, downloads and locked result tables |
| Layout | Seven active pages at 1440px, 820px and 390px widths, including overflow checks and screenshots |
| Errors and navigation | Loading/error displays, removed routes, navigation without implicit mapping, startup DB-failure handling |

The mobile admission result screenshot was also visually inspected: controls were
readable and the wide results table remained inside its scroll container.

## Test setup and evidence

- Frontend: `http://127.0.0.1:5178`.
- Fixture API: `http://127.0.0.1:8123`.
- Browser configuration: [playwright.site-audit.config.js](../../frontend/playwright.site-audit.config.js).
- Optional interactive report: `frontend/test-results/site-audit/browser-report/`.
- Optional screenshots and traces: `frontend/test-results/site-audit/browser-artifacts/`.

Commands used:

```powershell
# From frontend/
npx playwright test --config playwright.site-audit.config.js

# From backend/
uv run python -m unittest discover -s tests -p "test_*.py"
```

The existing user session was not used. The browser fixture backend stores sessions
in a separate temporary directory and replaces SQL repositories with test data.
Therefore this run verifies application behavior, not live database connectivity,
real school data, production deployment or large-file performance. Passing tests
do not establish every possible browser/input combination.

## Targeted SQL dump verification

The live counts below are historical results from before the current inner `JOIN`
change. They have not been revalidated against the live database for that change
and do not establish equality of row and student counts for every school.

The SQL dump correction was checked separately against the configured live database
and the local browser application:

- School indexes `22` and `25` returned `353/353` and `437/437` rows/unique student
  IDs respectively, with zero completely identical normalized rows.
- The Dump page showed matching **Dump records** and **Students** counts for index
  `22` (`353` each).
- Fetching nonexistent index `999999` displayed an error while retaining the loaded
  index `22` dump.
- The focused normalization and failed-fetch preservation tests passed.

A later full backend-suite run passed all 144 tests.

### Current admission inner-join verification

The current query includes school students (`user_type = '0'`) only when they have
a `paid_users` record. Multiple distinct admissions remain separate dump rows.
See [SQL dump selection and counts](MAPPING_WORKFLOW.md#sql-dump-selection-and-counts).

The focused command passed all 7 tests:

```powershell
uv run python -m unittest tests.test_admission_dump_service tests.test_dump_overview
```

The count test exercises 12 scenarios, including absent paid records, excluded
user types, other/NULL schools, repeated/distinct admissions, and missing-value
variants. It executes the production SELECT against isolated SQLite fixtures with
a registered `CONCAT_WS` function. This verifies row cardinality for those fixtures,
not MySQL collation behavior or live school counts.

The final backend verification includes the file-workflow API tests. Email tests now
follow the current single-pass first-name behavior, while full-name/class
tests reflect eligibility independent of admission number. The unused email-mapping
compatibility parameter was also removed.
