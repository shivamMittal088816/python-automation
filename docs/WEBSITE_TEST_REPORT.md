# Website test report — 24 September 2026

Reference: [Session and data flow](SESSION_AND_DATA_FLOW.md).

## Outcome

- **18 browser tests passed**, using a separate visible Edge browser and isolated fixture sessions.
- The production frontend build completed successfully.
- **128 backend tests passed**.
- No stale UI data was found in the covered browser scenarios. A regression test was
  added for failed/successful SQL dump replacement and result invalidation.

## Coverage

| Area | Verification |
|---|---|
| Session lifecycle | Cookie transport, creation, restoration, reload, reopening a tab and inactivity expiry |
| Saved school index | SQL fixture fetch restores the saved index after reload; unsubmitted typing does not overwrite it |
| SQL replacement | Failed lookup preserves the loaded dump/results; successful replacement clears stale downstream results |
| Files and storage | CSV/XLSX workflows, upload and local-path loading, saved identifiers, manifest persistence and source invalidation |
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
- Browser configuration: [playwright.site-audit.config.js](../frontend/playwright.site-audit.config.js).
- Interactive HTML report: [browser-report/index.html](../logs/site-audit/browser-report/index.html).
- Screenshots: `logs/site-audit/browser-artifacts/`.

Commands used:

```powershell
# From frontend/
npx playwright test --config playwright.site-audit.config.js

# From repository root, with TEMP/TMP pointed at the workspace .tmp folder
.\.venv\Scripts\python.exe -m unittest discover -s Backend/tests -p "test_*.py"
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

A later full backend-suite run passed all 128 tests.

### Subsequent admission left-join verification

The current query retains school students (`user_type = '0'`) even when they have
no `paid_users` record. Multiple distinct admissions remain separate dump rows.
See [SQL dump selection and counts](MAPPING_WORKFLOW.md#sql-dump-selection-and-counts).

The focused command passed all 7 tests:

```powershell
.\.venv\Scripts\python.exe -m unittest Backend.tests.test_admission_dump_service Backend.tests.test_dump_overview
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
