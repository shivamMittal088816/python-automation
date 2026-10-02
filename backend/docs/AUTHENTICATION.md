# Cookie authentication

The app supports account creation, sign-in, sign-out and authenticated workflow access. Workspace ownership, accepted memberships and active selection are linked to account IDs in the database; see [workspace switching](WORKSPACE_SWITCHING.md).

## Data

Application-owned tables (separate from external student/platform users):

- `app_users`: UUID, name, normalized unique email, salted password hash, active flag, creation/update timestamps.
- `auth_sessions`: SHA-256 digest of an opaque random cookie token, user ID, creation time, expiry and revocation time. The raw token is never stored in the database or returned in JSON.
- `auth_rate_limits`: hashed account/IP bucket keys and counters for shared, database-backed login/registration throttling.

Passwords use scrypt with N=131072, r=8, p=1, a random 16-byte salt and constant-time digest comparison. Hash work is bounded to two concurrent operations per worker. Password lengths are 15–128 characters at registration. Authentication errors do not echo passwords. These parameters follow [OWASP password storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).

## Routes and cookies

- `POST /api/v1/auth/register`: name/email/password; creates the account and issues a session.
- `POST /api/v1/auth/login`: email/password; rotates the browser session and revokes its previous token.
- `GET /api/v1/auth/me`: returns public account details (or null) and whether authentication is required.
- `POST /api/v1/auth/logout`: revokes the session and clears its cookie. Also clears workflow cookies to prevent another account inheriting the previous browser's workspace access.

The cookie is `auth-session`, or `__Host-auth-session` when secure cookies are enabled. It is HTTP-only, host-only, Path=/, SameSite as configured, Secure in HTTPS deployments, with a default 7-day expiry. Mutating authentication endpoints require an explicitly trusted Origin. Logout is idempotent; replayed, expired and revoked tokens cannot access protected workflow APIs. Disabled accounts are denied. Wrong/unknown-account login messages are identical.

`AUTH_REQUIRED=true` is the default. Workflow, invitation, workspace and student API routers require authentication; health endpoints remain public. Only authentication failures carry `X-Authentication-Required: 1`, so a missing workflow cookie does not falsely sign a user out. Frontend routes preserve invitation links and local return destinations through login, and reject external redirects. Local/session storage does not contain passwords or authentication tokens.

## Setup

Run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.upgrade_auth_schema
```

This additive migration was applied locally. Also run `python -m app.scripts.upgrade_workspace_schema` for account workspace tables and membership columns. Neither migration modifies external student data tables. Start the frontend and backend as usual and open `/login`; use Create an account for the first account. No seed/default credentials were created. Use `SESSION_COOKIE_SECURE=false` for local HTTP development; keep it true for production HTTPS. `AUTH_SESSION_HOURS` defaults to 168. Invitation codes expire after 72 hours; account memberships and workspace files persist until explicitly revoked, expired or removed.

Logout clears credentials while retaining account workspaces, memberships and preferences. Signing in restores those workspaces across browsers. Email verification and password reset are not implemented.

## QA

- Six authentication backend tests passed with authentication required: hashed passwords, HTTP-only/Secure cookie flags, protected API access, normalized email, generic login failures, token rotation, logout/replay, expiry, disabled users, duplicate emails, validation, CSRF, throttling and account changes.
- The complete backend suite passed 257 tests. Legacy workflow tests explicitly disable the auth guard in their isolated test process; authentication tests enable it.
- Four Edge auth browser tests passed with `AUTH_QA_REQUIRED=true`: login redirects/return paths, account creation, password visibility, cookie persistence, logout/replay, wrong password, keyboard submit, responsive layouts and external redirect rejection.
- Three workspace-switching browser regression tests passed after gating the bulk selector until initial workspace restoration completes.
- Login desktop and registration/login mobile screenshots visually inspected in `.test-temp/auth-qa/`.
- Frontend production build passed.

Authentication browser QA:

```powershell
$env:AUTH_QA_REQUIRED = 'true'
npx playwright test e2e/auth.spec.js --workers=1
```

Backend regression QA:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
```
