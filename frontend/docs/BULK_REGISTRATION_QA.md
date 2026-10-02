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

## Regression results and limits

Four focused browser checks passed across the verification runs:
independent file loading, temporary storage recovery, draft preservation across
tabs without BroadcastChannel, and full-file sanity checking/replacement.
Production build and patch whitespace checks passed.

The full historical bulk browser suite was not rerun in this pass. Earlier
coverage includes stale expectations for removed Verify emails/Verify usernames
controls and superseded result sections. The focused results above do not claim
that the full suite is green. Live SQL integrations, production data, and other
browser engines were not exercised.
