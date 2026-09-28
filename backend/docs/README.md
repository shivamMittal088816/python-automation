# Documentation index

Current startup commands for the updated folders: [Run the project](RUNNING.md).

Unless stated otherwise, paths in these documents are relative to the repository
root. The deployable applications are `frontend/` and `backend/`; Python commands
run from `backend/`, while npm commands run from `frontend/`.

## Current guides

- [Bulk registration conversion](BULK_REGISTRATION.md)
- [Clone, run, test, and deploy](CLONING.md)
- [Frontend/backend structure](STRUCTURE_MIGRATION.md)
- [Code flow](CODE_FLOW.md)
- [Mapping workflow](MAPPING_WORKFLOW.md)
- [Session and data flow](SESSION_AND_DATA_FLOW.md)
- [Cookie sessions and cross-origin deployment](COOKIE_SESSIONS.md)
- [Module guide](MODULE_GUIDE.md)
- [Database query reference](AUTOMATED_DUMP_RETRIEVAL_QUERY.md)
- [Error handling and production boundaries](ERROR_HANDLING.md)
- [GitHub publishing safety](GITHUB_SAFETY.md)
- [Current verification report](WEBSITE_TEST_REPORT.md)

## Historical reports

These record earlier cleanup, UI, or dependency work. Their historical test counts
and observations are retained as dated evidence; current commands, paths, and
verification totals are stated in the current guides above.

- [Post-migration cleanup report](CLEANUP_REPORT.md)
- [Unused-code cleanup report](UNUSED_CODE_CLEANUP.md)
- [Dependency modernization audit](DEPENDENCY_AUDIT.md)
- [Frontend UI refinement report](../../frontend/docs/UI_REFINEMENT.md)

## Current code-reference guides

- [External database contract](EXTERNAL_DATABASE_SCHEMA.md): explains application-owned
  versus platform-owned tables and lists the external columns consumed by repositories.
- [Code flow](CODE_FLOW.md): traces React, frontend services, FastAPI routes, services,
  repositories, responses, and UI updates.
- [Session and data flow](SESSION_AND_DATA_FLOW.md): describes the modular workspace
  hooks, cookie sessions, snapshots, revisions, and cross-tab synchronization.

## Bulk registration documentation

- [Bulk registration](BULK_REGISTRATION.md) explains file intake, conversion, username
  and email generation, verification, pagination, downloads, and its independent session.
- [Database queries](AUTOMATED_DUMP_RETRIEVAL_QUERY.md) explains its read-only school,
  section, username, and email queries.
- [External database contract](EXTERNAL_DATABASE_SCHEMA.md) explains ownership of the
  platform lookup tables.
