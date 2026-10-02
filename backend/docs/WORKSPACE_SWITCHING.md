# Account workspace switching

Workspace identity, ownership, membership and active selection are database-backed. The only browser credential issued to authenticated users is the HTTP-only `auth-session` cookie (`__Host-auth-session` with secure cookies). The cookie identifies an authentication session; it contains neither a workspace ID nor permissions.

## Tables and request resolution

- `workspaces`: workspace ID, public selection ID, workflow type, name, owner user ID, storage ID, creation time and optional deletion time.
- `workflow_members`: accepted invitee user ID, workspace ID, workflow type, current role, source invitation, joined time and optional expiry/revocation. A unique constraint prevents duplicate memberships for one user/workspace/workflow. Newly accepted memberships have no automatic expiry and no member cookie token.
- `user_workspace_preferences`: one active workspace ID per user and workflow, plus its update time.
- `auth_sessions`: hashed login token and its user ID, expiry and revocation.

Each protected workflow request resolves the authentication cookie to a user, reads that user's active preference, verifies ownership or a live membership, and enforces the current role. Changing a role or revoking membership in the database takes effect on the next request. An active preference alone never grants access.

## API and UI

- `GET /api/v1/workspaces?workflow=mapping` lists the account's owned and joined mapping workspaces; `bulk_registration` lists bulk workspaces.
- `POST /api/v1/workspaces` with `workflow` creates and activates another owned workspace, preserving previous spaces.
- `POST /api/v1/workspaces/select` with `workflow` and the public `workspace_id` validates access and stores the preference transactionally.
- Redeeming an invitation creates an account membership, selects the workspace and consumes the invitation in one database transaction. Self-invites are rejected across devices. Existing active memberships cannot be duplicated. A both-workflow invitation updates each workflow's membership and preference.

The dropdown uses real owner names and email addresses. Owners can see accepted invitees with their actual account names, email addresses, current role and status. Edit access remains a disabled placeholder as requested; there is no permission-editing endpoint.

Signing out revokes the login token and clears old cookies without deleting memberships or preferences. Signing in again, including from a fresh browser, restores the account's workspace selection and files. Preferences are shared across devices and tabs, with separate mapping and bulk selections. Workflow requests send their last observed `X-Active-Workspace`; stale selections receive HTTP 409 with `X-Workspace-Selection-Conflict: 1` and require a reload.

Invitation generation and member listing also carry the observed workspace context through `X-Mapping-Workspace` and `X-Bulk-Registration-Workspace`. Both-workflow invitations validate each context before issuing a link. A membership role of Owner never substitutes for the workspace's owner user ID.

Invitation codes expire after 72 hours and are single-use. Accepted membership remains valid until revoked or explicitly expired. Resetting/removing workspace data makes the old workspace unavailable to its members.

## Storage and setup

No previous anonymous browser session files are imported. Old unlinked SQL records do not grant account access.

Run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.upgrade_workspace_schema
```

The additive migration creates the workspace/preference tables and adds account membership columns and constraints. It was applied locally and can be rerun. It does not modify external student records.

Authentication and selection are no longer stored in browser-identity JSON files. Uploaded files, generated outputs and workflow settings still use filesystem storage under `backend/storage/workspaces/mapping` and `backend/storage/workspaces/bulk_registration`. Account workspace manifests are persistent and do not expire after 24 hours of inactivity. Existing file-operation locks remain process-local; multi-worker/host deployment still requires shared file storage and cross-process coordination.

## Validation

The complete backend suite passed 257 tests. After additional account-isolation tests and obsolete cookie resolver cleanup, all 29 targeted workspace/invitation/model tests passed. The final 16 workspace tests also passed, including two added checks for persistence beyond the old inactivity lifetime and member denial after an owner resets bulk storage. Coverage includes multiple memberships, personal workspace creation, account restoration across devices, independent workflow selections, live roles/revocation, self-invites from another device, duplicate membership protection, rejoining after revocation, stale tabs and rejection of copied legacy credentials.

All 14 authentication/invitation/workspace browser tests passed. All four authentication browser tests passed again after coverage was extended to verify uploaded-file restoration after logout/login and login from a fresh browser. Frontend production build passed. Workspace desktop/mobile screenshots in `.test-temp/invitation-qa/` were visually inspected.

The initial local schema upgrade succeeded. A later attempt to verify a second run could not connect because local MySQL was refusing connections; migration rerun verification remains pending until MySQL is running.
