# Error handling and production boundaries

## Application guarantees

The API converts expected failures into stable HTTP responses without returning
stack traces, database details, local paths, or parser internals to the browser.

| Status | Meaning |
|---|---|
| `401` | The workflow cookie is missing or invalid. |
| `403` | Request origin or local-path access is not allowed. |
| `404` | A session, file, result stage, or result group does not exist. |
| `409` | The session expired, saved state is inconsistent, a write is stale, or no result is currently available for an operation. |
| `413` | An uploaded or local-path file exceeds `MAX_UPLOAD_BYTES` (100 MB by default). |
| `422` | Input, file contents, selected sheets, columns, or mapping prerequisites are invalid. |
| `500` | An unexpected internal operation failed; the detailed exception is logged server-side. |
| `503` | A required database operation is temporarily unavailable. |

The global FastAPI exception handler logs unexpected exceptions and returns a
generic `500` response. Request IDs and `Server-Timing` headers are added to API
responses for operational tracing. Mutation failures do not publish the in-memory
workspace state, and stale revisions are rejected before mutation.

File boundaries include empty-file checks, extension validation, a configurable
size limit, safe parser errors, snapshot-reference validation, and atomic manifest
replacement. Result-download failures do not expose workbook or filesystem details.

The React application handles startup failures, operation failures, download
failures, asynchronous and synchronous request failures, stale revisions, session
expiry, unavailable browser storage, and unavailable `BroadcastChannel`. The top
level error boundary logs technical details to the browser console but renders only
a generic recovery message to the user.

## Verified failure cases

Automated tests cover missing/expired/invalid sessions, stale revisions, invalid
origins, missing files and result groups, invalid sheets and columns, empty and
oversized files, malformed workbooks, SQL lookup failures, unavailable databases,
mapping validation failures, corrupt result snapshots, failed session restoration,
cross-tab conflicts, network/UI failures, and responsive recovery states.

## Deployment responsibilities

Application error handling is only one part of production readiness. A deployment
must also provide:

- HTTPS, `SESSION_COOKIE_SECURE=true`, and explicit production `CORS_ORIGINS`;
- reverse-proxy request-size limits aligned with `MAX_UPLOAD_BYTES`;
- request timeouts appropriate for large XLSX processing and database queries;
- persistent session storage, backups where required, and capacity monitoring;
- shared locking/storage before running multiple API workers or servers;
- centralized logs and alerts keyed by `X-Request-ID`;
- database connection, timeout, least-privilege, and secret management policies;
- authentication and authorization before exposing school data to untrusted users;
- dependency/security scanning and a tested rollback/deployment procedure.

The current in-process workspace lock is suitable for one backend process. It is
not a distributed lock, so multiple production workers require coordinated locking
before they can safely mutate the same session.
