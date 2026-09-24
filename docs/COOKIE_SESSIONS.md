# Workflow session cookies

Workflow credentials are sent only in an HttpOnly cookie. Create a workspace with
`POST /api/v1/mapping/session` and retrieve it with `GET /api/v1/mapping/session`.
Other workflow endpoints retain their existing suffixes directly under
`/api/v1/mapping`, for example `/mapping/email-mapping/run` and
`/mapping/downloads/admission`. Old `/sessions/{id}` routes are removed.

The backend sets `__Host-student-mapping-session` with Secure, HttpOnly, SameSite=Lax, Path=/,
and no Domain. Production must use HTTPS. For local HTTP environments where
secure cookies are unavailable, set SESSION_COOKIE_SECURE=false; the development
cookie is then named student_mapping_session. Never use that setting in production.
The cookie lasts for the browser session; the existing server-side 24-hour
inactivity expiry remains authoritative.

Frontend fetch requests include credentials. Use the same hostname for the
frontend and backend (do not mix localhost and 127.0.0.1). Configure exact allowed
frontend origins in CORS_ORIGINS. Cross-site deployments are not supported by
this SameSite configuration. Unsafe requests from foreign origins are rejected.

The JSON workspace_id is a separate non-secret UI identifier; it cannot be used
to access a backend session. The old studentMappingSession storage key is removed
on startup. Cookies are shared across browser tabs, so tabs share the active
workflow. Uploads, settings, mapping algorithms, downloads, and inactivity expiry
retain their existing behavior. Named-school restore has since been removed;
new sessions start empty.

This change does not add login or school authorization. Those remain necessary
before exposing saved school data to untrusted production users.
