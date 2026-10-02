# Workspace names

The initial personal workspace opens a naming dialog when its owner first enters
the workflow. The dialog includes a live preview, supports keyboard submission,
and retains the entered name if saving fails. Once saved, setup does not reappear
on reload or another login. Mapping and bulk registration have separate workspaces
and each initial workspace is named when first used.

Create workspace in the dropdown opens the same dialog before creating any files
or database rows. Cancel leaves the current workspace and selection unchanged.
The pencil beside an owned workspace opens Rename workspace. Shared editors and
viewers cannot rename someone else's workspace.

## Storage and API

- `workspaces.name` is the single source for the display name.
- `workspaces.name_confirmed` records whether the initial naming step is complete.
  Automatically created workspaces start with this flag false; explicitly named
  creation and successful rename set it true.
- `POST /api/v1/workspaces` accepts `workflow` and `name`. Omitting the name remains
  supported for initial workflow setup and older API callers.
- `PATCH /api/v1/workspaces/{public_workspace_id}` accepts `{ "name": "School 2026" }`.
  The backend checks the authenticated account against the actual workspace owner.
- The owner’s workspace list includes `needs_name`. Shared rows use the current
  workspace name and owner information; no copy is stored in user or member records.

Names are trimmed, must contain 1–100 characters, and cannot contain ASCII control
characters. Duplicate names are allowed. Names are rendered as text and never used
as file paths or identifiers. Renaming preserves workspace IDs, uploaded files,
revisions, invitations, memberships and active selection. Dropdown data refreshes
when opened and when the browser window regains focus.

## Existing databases

Run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.upgrade_workspace_schema
```

The migration adds the flag without replacing workspace records. Existing automatic
`My workspace` names are offered the setup dialog; existing custom names remain
confirmed. The migration is safe to rerun and has been applied to the configured
local database.

Browser QA uses the isolated fixture server, SQLite and temporary file storage.
`workspace-naming.spec.js` covers first login, creation/cancellation, renaming an
inactive workspace, file preservation, shared editor authorization, mobile layout,
save failure/retry and keyboard cancellation. Existing authentication and workspace
switching scenarios also include the naming flow.

Validation completed on 2026-10-02: all 273 backend tests passed; production build
passed; 14 browser scenarios were exercised. Seven passed on the initial run and
the remaining seven passed after correcting an ambiguous test locator. Desktop
setup/rename and mobile setup screenshots were visually checked. The configured
database migration was applied and successfully rerun.
