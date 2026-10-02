# Code review and browser QA — 2 October 2026

Reviewed the modular authentication, invitation and workspace backend and their frontend clients, components and hooks. Browser flows used Edge through Playwright against the real FastAPI/React code with isolated SQLite accounts and temporary workspace files. Screenshots were manually inspected on desktop and a 390 × 844 mobile viewport. These checks did not modify real accounts or uploaded files.

## Findings and fixes

| Finding | Impact | Fix |
|---|---|---|
| Stale tabs sent workspace context for file APIs but not invitation generation/member listing | An old tab could issue an invitation for a different workspace selected elsewhere | Invitation calls carry the tab's observed workspace ID. Mapping and bulk contexts are checked independently, including both-workflow invitations. Conflicts return HTTP 409 before creation or listing. |
| Member rows could use the `owner` role even when the user was not the workspace owner | A malformed or manually changed member role could grant owner operations | Ownership comes from `workspaces.owner_user_id`. Non-owner memberships accept only Editor or Viewer; other roles fail with HTTP 403. No existing API could directly set a member to Owner. |
| Invitation role/workflow controls remained editable during generation | The displayed permission could disagree with the generated invitation | Disable role/workflow choices and copying while pending, clear the previous link and prevent duplicate submissions. |
| Create workspace silently returned when list loading failed before any data was available | The enabled recovery action did nothing | Only an actual selected row can trigger the already-selected guard; creation works without a loaded list. |
| Bulk refresh ignored role changes when file revision stayed the same | A newly downgraded viewer still saw enabled editing controls, although writes were blocked by the backend | Refresh state when the role changes as well as when workspace/revision changes. |
| Bulk header navigation exceeded the mobile viewport | Horizontal scrolling and partially hidden navigation | Wrap header navigation and give its heading a full row on mobile. The 390px layout fits without hiding overflow. |
| Shared workspace names contained a malformed middle-dot separator | Incorrect visible workspace label | Corrected the UTF-8 separator. |

The new context headers are `X-Mapping-Workspace` and `X-Bulk-Registration-Workspace`; they are allowed by CORS. Existing workflow file APIs retain `X-Active-Workspace`. Client context identifies the displayed selection; every request still authenticates the user and independently checks access.

## Browser and visual checks

| Scenario | Result |
|---|---|
| Unauthenticated redirect and preserving invitation return paths | Passed |
| Registration, cookie persistence, logout/replay, incorrect password and sign-in | Passed |
| Restore workspace/files after sign-in in the same and a fresh browser | Passed |
| Responsive auth layouts and external return URL rejection | Passed |
| Accepted invitees, current role and disabled Edit access placeholder | Passed |
| Self-invitation rejection without consuming the code for another user | Passed on final rerun |
| Full-link/code entry, editor file sharing and consumed-code rejection | Passed |
| Viewer controls and direct API write denial | Passed |
| Invalid/unknown codes, Escape, focus return and mobile join dialog | Passed |
| Mapping, bulk-only and both-workflow invitations | Passed |
| Recover from unavailable shared access with another invitation | Passed |
| Multiple joined workspaces, personal files and workspace creation | Passed |
| Bulk workspace switching and stale-tab file operations | Passed |
| Stale-tab invitation generation/member listing | Passed after fix |
| Pending invitation controls and copying | Passed after fix |
| Create workspace after a simulated list HTTP 503 | Passed after fix |
| Editor-to-Viewer refresh without file changes | Passed after fix |
| Revocation blocks the next request; create personal workspace afterward | Passed |
| Mobile bulk header and workspace dropdown | Passed after fix; screenshot inspected |

The combined 18-test browser run initially passed 16 and found mobile overflow; a separate self-invitation check hit a transient `ECONNRESET`. After the layout fix, all five targeted browser tests passed, including the previously interrupted self-invitation scenario. The connection-reset failure was rerun without adding retries or weakening assertions.

The four new review scenarios live in `frontend/e2e/review-qa.spec.js`. Membership changes for browser QA are performed through a fixture-only endpoint in `backend/tests/browser_fixture_server.py`; it is never registered on the production app. Production permission editing remains the requested placeholder.

## Verification and evidence

- Full backend suite: **266 tests passed**.
- Browser coverage: **18 unique tests exercised**, with the final five-test targeted rerun passing.
- Frontend production build: **passed** after the final layout fix.
- `git diff --check`: **passed**.
- Live MySQL: read-only connection succeeded; all seven required account/workspace/invitation tables were present. Browser mutation scenarios used isolated fixture data.
- Browser diagnostics captured console errors, failed requests, statuses and request IDs. No unresolved uncaught browser exception remained in the passing scenarios.

Screenshots, relative to the repository root:

- `.test-temp/review-qa/invitation-pending-desktop.png`
- `.test-temp/review-qa/shared-viewer-mobile.png`
- `.test-temp/review-qa/bulk-viewer-mobile.png`
- `.test-temp/invitation-qa/workspace-members-desktop.png`
- `.test-temp/invitation-qa/workspace-switching-desktop.png`

Uploaded workflow data still uses filesystem storage with process-local locks; multiple workers/hosts have not been validated by this QA. No database schema changes were needed for these fixes.
