# Workflow module guide

The existing Backend and frontend directory structure is unchanged. Modules are
grouped by responsibility within the existing folders. Mapping service rules,
HTTP endpoints, session storage format and response fields are unchanged.

## Backend responsibilities

| Module | Responsibility |
| --- | --- |
| `Backend/api/file_workflow_state.py` | Session creation, expiry, locking and workflow access |
| `Backend/api/file_workflow_session_storage.py` | Save and load session manifests and file snapshots |
| `Backend/api/session_cookie.py` | Session cookie handling and request-origin checks |
| `Backend/api/file_workflow_constants.py` | Input, stage and source names |
| `Backend/api/file_workflow_validation.py` | HTTP validation errors and required school identity |
| `Backend/api/file_workflow_snapshots.py` | Input registration, file reading and worksheet selection |
| `Backend/api/file_workflow_configuration.py` | Column suggestions and committed admission configuration |
| `Backend/api/file_workflow_responses.py` | Workspace summaries, run metadata and paged responses |
| `Backend/utils/workbook_operations.py` | Workbook conversion, status normalization and manual row transfers |
| `Backend/utils/table_queries.py` | Literal search, header lookup and pagination |
| `Backend/utils/school_statistics.py` | School identity inference and class/section statistics |
| `Backend/repositories/admission_dump_service.py` | Select school students, attach admissions with a left join, retain students without paid records and remove exact normalized duplicates |

SQL dump rows are not necessarily unique students. The repository retains multiple
distinct admissions; `school_statistics.py` reports distinct student IDs separately
from row counts. See [SQL dump selection and counts](MAPPING_WORKFLOW.md#sql-dump-selection-and-counts).

Route modules import the module that owns each operation. The existing
`file_workflow_helpers.py` and `file_workflow_route_helpers.py` files remain as
compatibility import facades, with no duplicate implementation. Existing service
imports and callers can continue using them.

Admission, email, full-name/class and account-uniqueness logic remains in the
existing `Backend/services` subfolders. Database queries remain in repositories;
request/response models remain in schemas. Frontend pages, components, hooks and
API clients retain their existing locations.

## Naming conventions

- Python modules use `snake_case` and name their responsibility.
- Workflow HTTP modules use the `file_workflow_` prefix; reusable utilities use
  descriptive names such as `table_queries` and `workbook_operations`.
- Keep an operation's implementation in its owning module. Compatibility files
  only re-export existing names.
- Retain existing Python function names and state keys where callers depend on
  them. React components continue using `PascalCase`; hooks retain the `use` prefix.

## Refactor verification

All 33 original top-level helper/session function bodies were compared using
Python ASTs and are identical after extraction. Mapping-service source files and
the complete OpenAPI schema also match the pre-refactor baseline.

All nine browser tests pass. The backend suite passed 118 of 119 tests on its
first run; one session-reload test encountered an intermittent Windows file
replacement permission error and passed on a targeted rerun. No test assertions
or mapping rules were changed for this refactor.
