# Authentication, invitation and workspace code

These features are organized by domain, with route handlers separated from validation, database queries and reusable operations.

```text
backend/app/
  auth/
    dependencies.py             # Origin checks and authenticated-user guard
    models.py                   # Account, login session and rate-limit tables
    schemas.py                  # Login and registration validation
    routes/
      __init__.py               # Router composition
      accounts.py               # Registration and sign-in endpoints
      sessions.py               # Current account and logout endpoints
    services/
      accounts.py               # Account creation and credential verification
      cookies.py                # Cookie naming and legacy-cookie cleanup
      passwords.py              # Scrypt hashing and verification
      rate_limits.py            # Login/registration throttling
      sessions.py               # Session resolution, rotation and issuance
      tokens.py                 # Token digests
  invitations/
    access.py                   # Enforce collaborator permissions
    schemas.py                  # Invitation request/response contracts
    repositories/
      invitations.py            # Invitation persistence
      members.py                # Accepted memberships joined to accounts
    routes/
      __init__.py               # Router composition
      generation.py             # Invitation creation endpoint
      join.py                   # Invitation acceptance endpoint
      members.py                # Owner-scoped member listing endpoint
    services/
      creation.py               # Generate invitation token and URL
      redemption.py             # Atomic membership and preference update
      members.py                # Public member details
  workspaces/
    models.py                   # Workspace and active-preference tables
    schemas.py                  # Create/select validation
    routes/
      __init__.py               # Router composition
      creation.py               # Create owned workspace endpoint
      listing.py                # Account workspace list endpoint
      selection.py              # Select workspace endpoint
    services/
      access.py                 # Ownership and current membership checks
      identity.py               # User/database context and public IDs
      listing.py                # Personal/shared workspace listing
      memberships.py            # Revocation and expiry status
      ownership.py              # Register owned workspace and select it
      preferences.py            # Per-user locking and preference updates
      storage.py                # Saved workspace data availability
  common/time.py                # UTC database timestamps
```

The domain `routes/__init__.py` files export the assembled routers used by `app/main.py`. Database dependency injection, API URLs, cookies, table definitions and permissions are preserved. Migration scripts and test fixtures import their helpers from the new modules. Obsolete monolithic implementations were removed after replacement checks passed.

Frontend structure:

```text
frontend/src/
  components/
    auth/                       # Account menu and protected route guard
    invitations/                # Invite/join dialogs and their styles
      utils/invitationToken.js  # Invitation code/link parsing
    workspaces/
      WorkspaceSelector.jsx     # Dropdown composition and interaction
      WorkspaceRow.jsx          # Personal/shared workspace row
      WorkspaceMembers.jsx      # Accepted-member display
      hooks/useWorkspaceSelector.js
                                # Loading, cancellation, create and switch
      workspace-selector.css
    layout/                     # General page layout, sidebar and skeleton
  services/
    auth/api.js                 # Current account, register, login and logout
    invitations/api.js          # Generate, join and accepted members
    workspaces/api.js           # List, create and select
    api.js                      # Shared HTTP transport and response handling
  context/AuthContext.jsx       # Account state and provider
  pages/Auth/
    AuthPage.jsx                # Login/registration presentation
    utils/returnDestination.js  # Safe local return destination
```

Workspace data hooks do not render UI. Row and member components do not issue HTTP requests. Shared HTTP behavior stays in `services/api.js` rather than being duplicated in feature clients. Permission editing remains a placeholder.

Validation: 263 backend regression tests, the final targeted account/invitation/workspace tests, 14 browser tests and the frontend production build. Source backups made before the refactor remain in `.test-temp/modularization-backup/` at the repository root.
