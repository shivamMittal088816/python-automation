# Workspace changes: code review and QA

Reviewed on 2026-10-03. No blocking defects were found in the reviewed changes.
No application code changes were needed during this QA pass.

## Code review

Reviewed the soft-delete route and service, workspace listing and access checks,
schema/index upgrade, API error parsing, removal recovery, deletion confirmation,
and the homepage, sidebar, and workspace selector styles.

- Only the actual owner can delete a workspace.
- Setting `deleted_at` and changing the owner's selection commit together; failures roll back.
- Repeating deletion preserves the original deletion timestamp.
- Files and related records remain retained, while deleted workspaces disappear from lists.
- The deletion-specific 410 code triggers recovery in both supported workflows.
- Switching after deletion stays within the same workflow and chooses the oldest available owned workspace.

## Browser walkthrough and visual review

Used headless Microsoft Edge with isolated fixture accounts and a temporary
database, followed by visual inspection of screenshots. This was a scripted
browser walkthrough, rather than an interactive human browser session.

Checked:

- School CSV upload, SQL dump fetch, school identity display, and admission mapping results.
- Sidebar opening, Escape dismissal, and keyboard focus restoration.
- Homepage, sidebar, and switcher layout at desktop width and 390px/320px mobile widths.
- Twelve long workspace names: truncation, internal list scrolling, and visible create/join actions.
- Delete confirmation cancellation with Escape.
- Owner deletion and automatic selection of another workspace.
- Member removal message and recovery to their personal workspace.

All 11 walkthrough checks passed. No uncaught browser page errors were captured.
No horizontal overflow was detected in the sidebar or switcher at the checked widths.

Local walkthrough evidence is under
`.test-temp/workspace-review-2026-10-03/`, including `results.json` and screenshots.

## Regression checks

- Backend deletion, switching, naming, and invitation regression suites: **40 tests passed**.
- Browser deletion/recovery suites: **9 tests passed**, covering both mapping and bulk registration,
  last-workspace deletion, retry/cancellation, operation/focus detection, and inactive shared deletion.
- Frontend production build: **passed**.

## Expected behavior and coverage limits

Members detect removal on their next API request or focus refresh. There is no
live push notification. If the owner deletes their last workspace, existing page
initialization creates a fresh workspace and may ask for its name.

This remains soft deletion: no purge job or automatic permanent deletion was added.
The browser checks used fixture data; production database concurrency and live
external integrations were not exercised in this pass.
