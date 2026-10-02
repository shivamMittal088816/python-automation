# Bulk registration UI review and QA

Reviewed on 2026-10-03. No blocking defects remain in the reviewed UI changes.

## Findings and corrections

- The generated preview displayed **Ready to export** before final verification
  enabled downloads. Changed the badge to **Preview generated** so the status
  describes the current state accurately.
- The draft-entry browser test typed while the workspace was still opening.
  Added an explicit wait for the school field to be enabled.
- The sanity browser test could upload while its input was disabled. Added a
  readiness wait and confirmation that the file loaded. Updated its stale
  expectation from 9 passing checks to the current 11.

Reviewed the compact page markup, scoped stylesheet, output-settings disclosure,
preview status, error states, and existing workflow guards. Conversion and
verification logic were not changed.

## Browser walkthrough and visual review

Used Playwright with headless Microsoft Edge, isolated fixture accounts, and a
temporary database. Visually inspected desktop, tablet, and mobile screenshots.
This is a scripted browser walkthrough and screenshot review, not an interactive
human browser session.

Passed:

- Invalid school input disables verification; unknown school errors recover after correction.
- School verification, CSV upload, input sanity checks, and preview generation.
- Output-settings expansion/collapse and all seven predefined values.
- Keyboard Enter toggles settings; Escape dismisses the join dialog.
- Rules navigation and return to the workspace preserve loaded data.
- A second tab restores the verified school and loaded file.
- Final verification passes and enables successful CSV and XLSX downloads.
- Reset cancellation preserves the loaded file.

Checked widths: **1366, 1100, 1099, 1024, 901, 900, 768, 641, 640, 390, and 320px**.
No horizontal overflow was detected with settings expanded or collapsed. No
uncaught page errors were captured. At 1366x640 the conversion action is visible;
smaller screens retain vertical scrolling.

Local evidence: `.test-temp/bulk-review-2026-10-03/` contains screenshots,
`results.json`, and the downloaded fixture files.

## Full regression follow-up

The local regression follow-up replaces older Verify emails/Verify usernames
tests with **Bulk-reg verify**, grouped review records, blank account fields,
and downloads disabled until successful final verification. Successful download
fixtures now include the required school, name, class, section, and gender data.

Mapping tests now recognize both Add and Replace file controls. Loaded-file
assertions match the current upload, path, and SQL source presentations. Tests
wait for enabled controls before editing or uploading during first-use setup.
The browser fixture's username allocator now returns candidates absent from its
simulated database and unique within the allocation. The standard Playwright
configuration starts Vite directly, preserving port flags on Windows.

The full run also exposed a product race: a delayed bulk operation could clear a
workspace-selection conflict after another tab reset the workspace. The hook now
retains that conflict until reload or an accepted reset in the same tab, rejecting
late operation responses and background reads. Tests confirm that the stale tab
stays disabled and reload restores the new selection; temporary read failures
can still recover normally.

- Full backend regression suite: **282 tests passed**.
- Full local browser suite: **82 scenarios exercised**. Initial run: 69 passed,
  13 failed. After corrections, all 13 failures and two related refresh checks
  passed in a **15-test rerun**. All 82 scenarios have passing coverage across
  these runs; this does not claim one uninterrupted all-green run.
- Final late-response and overlapping-refresh verification: **3 tests passed**.
- Production build and patch whitespace checks: **passed**.

Local logs are `.test-temp/full-backend-regression.log`,
`.test-temp/full-browser-regression.log`, and
`.test-temp/final-browser-regression.log`. Playwright captures diagnostics per
scenario under `frontend/test-results/` (ignored by Git).

The configured local suite excludes `e2e/live/`. Live SQL integrations,
production data, deployments, and other browser engines were not exercised.
