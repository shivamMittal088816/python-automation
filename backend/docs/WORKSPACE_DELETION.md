# Workspace soft deletion

Owners can delete their mapping and bulk-registration workspaces from the
workspace selector. The confirmation removes access immediately for everyone.

`DELETE /api/v1/workspaces/{workspace_id}` accepts the public workspace ID.
It returns `id`, `deleted_at` (UTC), and `active_workspace_id`. Only the actual
owner can delete a workspace. Repeated deletion succeeds without changing the
original deletion timestamp. Unknown IDs return 404; non-owners receive 403.

Deletion sets `workspaces.deleted_at` in a database transaction. Files,
invitations, memberships, and the workspace row remain intact. Deleted workspaces
are hidden from owned and shared lists, cannot be selected, and existing
collaborators' requests and invitation redemption are rejected.

Workspace access returns HTTP 410 with detail code `workspace_removed` for a
soft-deleted record. The frontend shows "Workspace removed" and explains that
the owner deleted it, replacing the old mapping or bulk-registration forms.
"Select workspace" opens the selector to switch to another workspace or create
one. Detection occurs on the next request, including initial load, operations,
or an existing focus refresh; no polling or push notifications are added.
Other access failures keep their existing messages.

When deleting the owner's active workspace, the service selects the oldest
remaining available owned workspace of the same workflow, or removes the owner's
selection if none remains. Other workflow selections are unaffected. Collaborator
preferences remain as references, but their deleted selection is reported as null
and access is rejected. They can select another workspace or create one.

The UI reloads after deleting the active workspace. Existing page initialization
may create an empty workspace when no selection remains.

New databases include `ix_workspaces_deleted_at`. For an existing database, run
the idempotent workspace schema upgrade from the backend directory:

```powershell
.venv\Scripts\python.exe -m app.scripts.upgrade_workspace_schema
```

This change provides no restore endpoint, purge job, or automatic permanent
deletion after 30 days. The existing bulk-registration reset endpoint retains
its separate reset behavior, which deletes files and creates a replacement.
