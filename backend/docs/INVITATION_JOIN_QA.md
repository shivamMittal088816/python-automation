# Invitation code joining and QA

Verified on 2 October 2026 (Asia/Calcutta).

Users can open **Join with invitation code** from the mapping sidebar or bulk
registration page. Short invitation links prefill the same dialog. Submitting a
valid code binds membership to the logged-in account and selects the shared
workspace in the database. No separate member cookie is issued.

The entry field also accepts a pasted full invitation link. It extracts the code
from `/i/<code>`, `/i/b/<code>`, or a supported legacy workflow URL with an
`invite` query parameter. Only the code is sent to the current backend; the
pasted link is never fetched. The input accepts up to 2048 characters so longer
links are not truncated.

Mapping, bulk registration, and both-workflow invitations are supported. Editor
members can change shared files. Viewer members get disabled editing controls,
and the API rejects write operations with HTTP 403. Configuration previews are
read-only and remain available. Only owners can issue invitations or reset a
shared bulk workspace.

Redemption checks the token hash, revocation, expiry, remaining uses, and whether
the referenced workspace still exists. A database row lock makes consuming a
single-use invitation and creating member records one transaction. Invalid codes
return 404, expired/revoked invitations return 410, and consumed codes return 409.

Self-invitations and duplicate active membership are rejected with HTTP 409
before consuming the invitation. Ownership and existing membership are checked
against the authenticated account ID, including across browsers and devices.
A both-workflow invitation is rejected if the account owns either target.

## Schema setup

The additive schema update was applied to the local database. It adds nullable
`bulk_workspace_id` to `workflow_invitations`, permits `both` in `workflow_type`,
and creates `workflow_members` if missing. `mapping_types` is not required.
For another deployment, run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.upgrade_invitation_schema
.\.venv\Scripts\python.exe -m app.scripts.upgrade_workspace_schema
```

Invitation codes last 72 hours. Accepted account memberships and workspace data
persist until explicitly revoked, expired or removed. A recipient whose access
is unavailable can select another workspace or enter a new invitation from the
workspace error screen. See [account workspace switching](WORKSPACE_SWITCHING.md)
for the current architecture and validation; the table below records earlier QA.

## Verification

| Check | Result |
|---|---|
| Backend regression suite | 236 tests passed |
| Invitation browser suite in Edge | 7 tests passed |
| Frontend production build | Passed |
| Live MySQL generation and joining in separate browser profiles | Passed |
| Two concurrent redemptions against MySQL | One HTTP 200 and one HTTP 409 |
| Live editor credential and read-only configuration preview | Passed |
| Editor changes visible to owner | Passed on disposable browser-test storage |
| Viewer API write rejection | Passed on disposable browser-test storage |
| Expired/revoked/unknown/used codes and revoked membership | Passed |
| Mapping, bulk, both, and recovery from unavailable access | Passed |
| Keyboard focus, Enter submission, Escape, focus restoration | Passed |
| Desktop 1366x768 and mobile 390x650 visual review | Passed |

The initial browser QA found that input autofocus was unreliable. The dialog now
explicitly focuses the code input after opening; the corrected case passed.

The live exploratory browser session used automated browser actions followed by
direct screenshot review. Screenshots: [desktop dialog](../../.test-temp/invitation-qa/desktop-join.png),
[mobile dialog](../../.test-temp/invitation-qa/mobile-join.png),
[invalid input](../../.test-temp/invitation-qa/invalid-code.png), and
[viewer workspace](../../.test-temp/invitation-qa/viewer-workspace.png).
Its action log is [manual findings](../../.test-temp/invitation-qa/manual-findings.txt).

Automatic approval review rejected an additional live clear-file mutation test
because of possible workspace data loss. Final live QA avoided file mutation;
editor mutations and direct viewer write attempts were verified on isolated,
temporary test workspaces instead.
