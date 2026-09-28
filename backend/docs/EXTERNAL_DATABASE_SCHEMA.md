# External database contract

This service reads several tables owned by the existing platform database. It does
not create, migrate, or alter those tables. The authoritative schema remains in the
platform database; this document records only the columns required by this service.

## Ownership boundary

`backend/app/models/student_model.py` defines the application-owned `students` ORM
table. Running `backend/app/scripts/init_db.py` may create that table through
`Base.metadata.create_all()`.

The following tables are externally managed and intentionally have no SQLAlchemy
model in this repository:

- `users`
- `paid_users`
- `users_schools`
- `users_sections`

Repositories access these tables through parameterized SQL. Adding incomplete ORM
models would incorrectly suggest that this application owns their schema and
migrations.

## Tables and consumed columns

### users

The mapping and bulk-registration workflows consume identifiers, names, account
details, school/class placement, and status fields from `users`. The exact subset
depends on the repository query. Important consumed columns include:

- `user_id`, `user_name`, `user_firstname`, `user_lastname`, `user_fullname`
- `user_email`, `user_mobile`, `user_gender`
- `user_edu_school`, `user_edu_class`, `user_edu_major`
- `user_package`, `user_status`

Used by `user_student_repository.py`, `username_repository.py`,
`email_repository.py`, `admission_dump_service.py`, and `email_dump_service.py`.

### paid_users

The admission dump joins `paid_users` to `users` using `user_id`. The workflow reads
the admission-number relationship required to match an uploaded school record with
an existing account.

Used by `admission_dump_service.py`.

### users_schools

The service uses `school_id` and `school` to validate a school index and obtain the
school name used by mapping and bulk-registration output generation.

Used by `admission_dump_service.py` and `bulk_registration.py`.

### users_sections

The service reads `section_id` and `section` to translate source section labels into
the canonical identifiers expected by bulk registration.

Used by `section_repository.py` and the bulk-registration section mapping.

## How to inspect the authoritative schema

Run these read-only statements against the configured MySQL database:

```sql
SHOW CREATE TABLE users;
SHOW CREATE TABLE paid_users;
SHOW CREATE TABLE users_schools;
SHOW CREATE TABLE users_sections;
```

For a shorter column listing:

```sql
DESCRIBE users;
DESCRIBE paid_users;
DESCRIBE users_schools;
DESCRIBE users_sections;
```

Do not copy guessed types, defaults, indexes, or nullability into this repository.
If this service later becomes responsible for these tables, add authoritative models
and versioned migrations as a separate ownership change.

## Related application layers

```text
FastAPI route
    -> service/business logic
    -> repository parameterized SQL
    -> externally managed MySQL table
    -> repository result
    -> response schema or workflow summary
```

Pydantic classes under `backend/app/schemas` describe HTTP payloads. They are not
database table definitions. Bulk-registration output columns under
`backend/app/mappings/bulk_registration/output_schema.py` describe an exported file,
not a database table.

## Bulk registration use of external tables

Bulk registration reads `users_schools` to validate the school and build generated email
domains, `users_sections` to resolve section labels, and `users.user_name`/
`users.user_email` to allocate and verify account values. These are parameterized reads;
the workflow does not insert, update, migrate, or create any platform-owned table.
