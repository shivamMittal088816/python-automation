# Code cleanup and database queries

The cleanup preserves application behaviour, comments, migration scripts, public
imports used by routes/tests, and the development cookie mode. Live ownership,
membership, expiry and revocation checks still run for every request.

Removed unused executable Loguru configuration and its runtime dependency,
the uncalled `blank_first_name_records` compatibility helper, the uncalled
`store_exports` wrapper, the retired spreadsheet password formula constant,
unused route imports and the obsolete workspace “soon” badge style. Legacy logger
comments remain in place. Password generation and exports continue using their
existing implementations. The lock file was regenerated offline and dependencies
were synchronized from it.

Database changes:

- Resolve a valid authentication session and active user with one joined SELECT,
  loading only the identity fields required by requests, without the password hash.
- Reuse the selected workspace access when checking collaborator permissions in
  the same request, avoiding duplicate preference, workspace and membership reads.
  This is not a cache shared between requests.
- Skip the previous-workspace COUNT query when creating an explicitly named space.
  Automatically named workspaces retain the original numbering behaviour.
- Read only public user identity fields when listing workspaces and accepted members.

`test_database_efficiency.py` checks SQL query counts for authentication and shared
mapping/bulk access, omission of password hashes from authentication reads, and
absence of COUNT queries for named creation. Existing authentication, invitation,
workspace and file-processing tests verify behaviour.

Frontend static analysis found no unused declarations or unreferenced exported
functions in the application sources. Backend import analysis distinguishes unused
imports from intentional re-exports and model registration.

Validation on 2026-10-02: all 277 backend tests and 14 browser scenarios passed.
The frontend production build and whitespace checks passed. Browser scenarios
covered login/logout, workspace naming, file preservation, invitation access,
role/revocation changes, workspace switching, stale tabs and mobile layout.
