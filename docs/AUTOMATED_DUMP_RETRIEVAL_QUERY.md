# Database queries: implementation and execution flow

This document covers all explicit database query types in the current Backend
application, plus the optional schema initialization script. Test-fixture SQL and
SQLAlchemy/PyMySQL internal connection or metadata operations are not application
retrieval queries. The application uses MySQL through SQLAlchemy and PyMySQL.

## Query inventory

| Query | Tables | Trigger / implementation | Guide |
|---|---|---|---|
| School name lookup | `users_schools` | Admission fetch: `fetch_school_dump()`, `SCHOOL_NAME_QUERY` | [Admission](#admission-dump) |
| Admission dump SELECT | `users`, `paid_users` | Admission fetch: `fetch_school_dump()`, `SCHOOL_DUMP_QUERY` | [Admission](#admission-dump) |
| Email lookup, repeated per batch | `users` | Email mapping: `fetch_email_dump()`, `QUERY` | [Email](#email-dump) |
| Student browse SELECT, with optional cursor | `users` | `UserStudentRepository.get_students()` | [Student browsing](#student-browsing) |
| `SELECT 1` | None | Application startup: `check_database_connection()` | [Connection and schema](#connection-and-schema) |
| Generated schema checks / CREATE TABLE / CREATE INDEX | `students` | Optional `Backend/scripts/init_db.py` | [Connection and schema](#connection-and-schema) |

The first five entries are read-only runtime query types. The startup `SELECT 1`
is a separate connection check. Only the optional initialization
script creates database objects.

## How the workflows connect

1. Backend startup checks the database connection once. A failed check logs a
   warning while allowing file-only workflows to remain available.
2. **Fetch from SQL** validates the school in `users_schools`, then retrieves its
   student accounts from `users` with admissions attached from `paid_users`.
3. Admission mapping operates on saved school/dump files in Python. It does not
   issue another database query for each student.
4. Email mapping takes rows directly from the school file and queries `users` for
   their email addresses in batches. Python then classifies the results.
5. Full-name/class mapping uses the school file and saved admission dump; it does
   not fetch database records in its mapping route.
6. The student browsing endpoint independently pages through `users`; it is not
   the school-filtered admission dump.

## Table roles

| Table | Role |
|---|---|
| `users_schools` | School identity and name for admission-fetch validation |
| `users` | Existing accounts: student details, school, class, package and email |
| `paid_users` | Admission numbers attached by `user_id` |
| `students` | Separate ORM table created by the optional initialization script; not used by these retrieval queries |

Query parameters such as `:school_index`, `:cursor`, `:limit` and `:emails` are
bound by SQLAlchemy. They are not literal MySQL syntax to paste unchanged into
an editor without parameter support. Email lists use an expanding bind parameter.
No database credentials are included in these documents.

The admission guide includes a manual count query for diagnosis. It is explicitly
labelled as an example and is not executed by the application.

[Session and data flow](SESSION_AND_DATA_FLOW.md) |
[Mapping workflow](MAPPING_WORKFLOW.md)

---

<a id="admission-dump"></a>

# Automated admission dump retrieval: queries, tables and flow

Source: `Backend/repositories/admission_dump_service.py`.
Endpoint: `POST /api/v1/mapping/student-dump/fetch`.

The application validates the entered numeric school index and binds it to
`:school_index` in both queries using SQLAlchemy parameters.

This guide covers all SQL executed by the admission dump fetch: the school-name
lookup and the student/admission query. Email mapping
has a separate database lookup and is outside this admission-fetch flow.

## Tables used

| Database table | Alias in SQL | Purpose | Columns used |
|---|---|---|---|
| `users_schools` | `us` | Confirm the school exists and retrieve its name | `school_id`, `school` |
| `users` | `u` | Supply the students and their account details | `user_id`, `user_edu_school`, `user_type`, `user_firstname`, `user_lastname`, `user_name`, `user_edu_class`, `user_edu_major`, `user_package`, `user_email` |
| `paid_users` | `pu` | Supply admission numbers for each student | `user_id`, `admission_number` |
Both `users_schools.school_id` and `users.user_edu_school` are compared with the
entered index in separate queries. The join between students and paid records is
`users.user_id = paid_users.user_id`; it does not join on school index.
These queries only read the database; they do not modify any of these tables.

## Step-by-step flow

1. **Validate the input.** Trim surrounding whitespace and require an ASCII numeric
   school index, such as `914`. Invalid input stops before database access.
2. **Find the school** in `users_schools` using that index. If no school name is
   returned, or the name is blank, fetching stops with an error.
3. **Select students from `users`** where:

   ```sql
   user_edu_school = :school_index
   AND user_type = '0'
   ```

   Other user types, including NULL, are excluded even when their school matches.
4. **Look up admission numbers in `paid_users`** using `user_id`. The inner `JOIN`
   excludes students without paid records.
5. **Build the output columns.** Return student details, admission number,
   `fullname` and the name/class matching key `generated_col`.
6. **Remove identical rows.** SQL `DISTINCT` removes duplicate selected rows.
   Python then converts NULL cells to empty strings and removes rows that become
   identical after that conversion. This does not merge all rows for one student.
7. **Save the result.** For a nonempty result, save a CSV snapshot and school
   metadata in the session. The displayed fetch count is the number of output rows.

Successful nonempty flow:

Enter school index ? Validate input ? Find school ? Select students ? Attach paid admissions ? Filter admissions ? Build columns ? Remove exact duplicates ? Save CSV snapshot.

The diagram shows the successful nonempty path. Invalid input, a missing school
or a database failure leaves the previous dump/results intact. A successful fetch
with zero students clears the previous dump and admission exports, saves the
school search settings, and reports that no student records were found.

## Query 1: school validation

The school must exist and have a nonempty name before the dump is fetched.

```sql
SELECT school FROM users_schools AS us WHERE us.school_id = :school_index
```

## Query 2: admission dump retrieval

```sql
SELECT DISTINCT
    u.user_id,
    CONCAT_WS(' ', u.user_firstname, u.user_lastname) AS fullname,
    pu.admission_number,
    u.user_name,
    u.user_edu_class,
    u.user_edu_major,
    u.user_firstname,
    u.user_lastname,
    u.user_package,
    u.user_email,
    LOWER(
        REPLACE(
            CONCAT_WS(
                ' ',
                u.user_firstname,
                NULLIF(u.user_lastname, ''),
                CASE
                    WHEN u.user_package = 14 THEN u.user_edu_class
                    WHEN u.user_package = 12 THEN u.user_edu_class + 1
                    WHEN u.user_package = 11 THEN u.user_edu_class + 2
                    ELSE u.user_edu_class
                END
            ),
            ' ',
            ''
        )
    ) AS generated_col
FROM users u
JOIN paid_users pu ON u.user_id = pu.user_id
WHERE u.user_edu_school = :school_index
AND u.user_type = '0'
```

There is no additional admission-validity subquery. Every row produced by the
inner join is eligible, and multiple distinct admissions are retained.

### Output columns and their sources

| Dump column | Source or calculation |
|---|---|
| `user_id` | `users.user_id`: student account identifier |
| `fullname` | First and last names joined with a space using `CONCAT_WS` |
| `admission_number` | `paid_users.admission_number`, blank after normalization if SQL NULL |
| `user_name` | `users.user_name`: account username |
| `user_edu_class` | `users.user_edu_class`: stored class value, unchanged |
| `user_edu_major` | `users.user_edu_major`: used as the section in the dump overview |
| `user_firstname` | `users.user_firstname` |
| `user_lastname` | `users.user_lastname` |
| `user_package` | `users.user_package` |
| `user_email` | `users.user_email` |
| `generated_col` | Lowercase first name + last name + adjusted class, with spaces removed |

`generated_col` uses the following class adjustment only for its matching key:

| Package | Class used in `generated_col` |
|---|---|
| `14` | Stored class |
| `12` | Stored class + 1 |
| `11` | Stored class + 2 |
| Other values, including NULL | Stored class |

For example, first name `Asha`, last name `Rao`, stored class `5`, and package
`12` produce `fullname = 'Asha Rao'` and `generated_col = 'asharao6'`. The output
`user_edu_class` remains `5`. `CONCAT_WS` skips NULL arguments.

`user_edu_school` and `user_type` filter the records but are not selected as dump
columns. School index/name are saved separately as snapshot metadata.

## Example: the two Excel tabs

Think of `users` as the student tab and `paid_users` as the admission lookup tab.
The application keeps the selected student population and attaches admissions by
user ID. Unlike a lookup returning one cell, this join retains every distinct
admission that meets the filter.

All students below belong to the entered school and have `user_type = '0'`:

| Student | Admission entries in `paid_users` | Final dump rows |
|---|---|---|
| A | `001` | One row: `001` |
| B | No paid record | Excluded by the inner join |
| C | `002`, `002` | One row: `002` |
| D | SQL NULL, empty text, `003` | One row: `003` |
| E | `004`, `005` | Two rows: `004` and `005` |
| F | SQL NULL, empty text | One row: blank admission |

Student E is represented twice. SQL NULL becomes empty text in Python; other
representations remain distinct unless the complete normalized rows are identical.

## Comparing counts with the database

For manual verification, count the same student population:

```sql
SELECT COUNT(*) AS school_student_count
FROM users
WHERE user_edu_school = :school_index
  AND user_type = '0';
```

This count query is a diagnostic example; the fetch endpoint does not execute it.
`:school_index` is an application-bound parameter. In a SQL editor without named
parameter support, replace it with the intended school index, for example `914`.

Assuming `users.user_id` uniquely identifies each student, compare this count with
the dump's **Students** count (distinct user IDs) at the same database state.
**Dump records** and the fetch message count retained rows and can be larger.
Counting school users without `user_type = '0'` includes a different population.
SQL collation affects which admission strings `DISTINCT` considers equal; no
`ORDER BY` is specified, so output order is not guaranteed.

## Python processing and saved data

After Query 2, the repository constructs a text DataFrame and normalizes it:

```python
frame = pd.DataFrame(result.fetchall(), columns=list(result.keys()), dtype=str)
frame = frame.fillna("").drop_duplicates().reset_index(drop=True)
```

The route converts a nonempty frame to CSV bytes and saves it as
`school_<index>_dump.csv` in the session snapshot system.

- Select students for the provided school index with `user_type = '0'`.
- Attach admission numbers by `user_id` using an inner `JOIN`; students without
  paid records are excluded.
- Keep multiple distinct admission numbers as separate rows; no first/latest
  record or conflict flag is selected.
- Read columns as text to preserve leading zeros, replace SQL NULL with empty
  text, and remove completely identical normalized rows in pandas.
- Dump records count rows; Students counts distinct user IDs. Different admissions
  or missing-value representations can produce multiple rows for one student.
- Save the fetched result as a snapshot. Fetch again to reflect database changes
  using the current inner-join selection.

These SQL rules apply when using **Fetch from SQL**. Uploading a CSV/XLSX dump
does not run these queries or reconcile the uploaded rows with the database.

## Implementation references

- [Query definitions and normalization](../Backend/repositories/admission_dump_service.py)
- [Fetch endpoint and snapshot replacement](../Backend/routes/file_workflow_routes/file_inputs.py)
- [Distinct student count and overview](../Backend/utils/school_statistics.py)
- [Session and data flow](SESSION_AND_DATA_FLOW.md)
- [Mapping workflow](MAPPING_WORKFLOW.md#sql-dump-selection-and-counts)

---

<a id="email-dump"></a>

# Email dump query

## Implementation and trigger

- [Repository](../Backend/repositories/email_dump_service.py): `QUERY` and `fetch_email_dump(values)`.
- [Route](../Backend/routes/file_workflow_routes/email_mapping.py): `email_map()`.
- Default endpoint: `POST /api/v1/mapping/email-mapping/run`.
- [Classification](../Backend/services/email_mapping/email_row_classification.py): Python matching after retrieval.

## Table and columns

Only `users` is queried, with alias `u`. The output contains `user_id`, `user_name`,
`user_edu_class`, `user_edu_major`, `user_firstname`, `user_lastname`, `user_package`,
`user_email` and `user_edu_school`. There is no join to `paid_users` and no admission
number in this query.

## SQL used

```sql
SELECT DISTINCT u.user_id, u.user_name, u.user_edu_class, u.user_edu_major,
u.user_firstname, u.user_lastname, u.user_package, u.user_email, u.user_edu_school
FROM users u WHERE LOWER(u.user_email) IN :emails
```

The repository constructs this with `text(...).bindparams(bindparam("emails",
expanding=True))`. SQLAlchemy expands the list into bound values for the `IN`
clause rather than interpolating addresses into SQL.

## Execution flow

1. The route requires the school file; Admission results are not required.
2. Read the selected email and first-name columns directly from the school file.
3. In `fetch_email_dump()`, discard missing/empty inputs, trim surrounding
   whitespace, lowercase addresses, remove duplicates and sort the unique list.
4. If the list is empty, return an empty DataFrame with the expected columns;
   no database query runs.
5. Execute the SELECT for batches of at most 500 distinct email addresses using
   one connection. For 1,001 addresses, three executions are needed.
6. Combine rows, read values as text, replace NULL cells with empty text and
   remove identical rows.
7. Python compares email and first name and applies duplicate/account rules.
   Matching school identity is checked during classification, not in this SQL.
   A candidate that otherwise matches but belongs to a different school goes to
   Review rather than Matched.
8. Save a separate `email_dump.csv` snapshot and grouped email result workbooks.
   The admission dump remains available.

## Important behavior

- SQL searches across all schools and all user types: there is no school-index
  or `user_type = '0'` filter here.
- SQL lowercases stored emails but does not trim them. Input addresses are trimmed;
  stored surrounding whitespace can therefore affect lookup behavior.
- Multiple accounts may share an email; `DISTINCT` removes identical selected
  rows, not all rows sharing an email. Ambiguous candidates are handled in Python.
- No `ORDER BY` is specified. Result order is not guaranteed.

---

<a id="student-browsing"></a>

# Student browsing queries

## Implementation and tables

- [Repository](../Backend/repositories/user_student_repository.py): `UserStudentRepository.get_students(cursor=None, limit=25)`.
- [Route](../Backend/routes/student_mapping.py): `get_students()`.
- Default endpoint: `GET /api/v1/mapping/students`.
- Table: `users`, without an alias or join.

## First page

When `cursor` is absent or `0`, the assembled query is:

```sql
SELECT
    user_id,
    user_firstname,
    user_lastname,
    user_email,
    user_edu_class,
    user_package
FROM users
ORDER BY user_id ASC
LIMIT :limit
```

## Following pages

When `cursor` is truthy, the repository inserts a WHERE condition:

```sql
SELECT
    user_id,
    user_firstname,
    user_lastname,
    user_email,
    user_edu_class,
    user_package
FROM users
WHERE user_id > :cursor
ORDER BY user_id ASC
LIMIT :limit
```

These are two forms of one dynamically assembled query, not two queries executed
for the same request. `cursor` and `limit` are bound parameters.

## Execution flow

1. The route validates `cursor >= 0`, if supplied, and `1 <= limit <= 100`.
   The default limit is 25.
2. The request receives a database session through `get_db`.
3. The repository builds the base SELECT, optionally adds `user_id > :cursor`,
   and appends ascending ID order and the limit.
4. Execute once and convert result mappings to dictionaries.
5. Return the last returned `user_id` as `next_cursor`; an empty page returns
   `next_cursor = None`. The route transforms the records with its response DTO.
6. Pass the returned cursor in the next request to continue after that ID.

For example, if a page ends at ID 150, the next query uses `user_id > 150`.
IDs need not be consecutive. There is no OFFSET or separate total-count query.
Even a final nonempty page returns its last ID; the next request may be empty.

Despite the endpoint name, this query has **no school or user-type filter**.
Its count must not be compared directly with the school-filtered admission dump.
It reads `users`, not the separate ORM table named `students`.

---

<a id="connection-and-schema"></a>

# Connection check and optional schema initialization

## Startup connection query

[Implementation](../Backend/main.py): `check_database_connection()`, called
from `lifespan()` through `run_in_threadpool`.

```sql
SELECT 1
```

1. Open a connection from the configured engine.
2. Execute this constant SELECT; it reads no application table.
3. Close/return the connection after the context exits.
4. Log success, or catch `SQLAlchemyError` and log a warning while allowing the
   application to start for file-only work.

This confirms connectivity at startup. It does not validate the three retrieval
tables, their data, or continued connectivity for later requests. The HTTP health
route returns a static response and does not repeat this SQL check.

[Engine configuration](../Backend/config/database.py) enables
`pool_pre_ping=True`. SQLAlchemy/PyMySQL can also perform connection health and
initialization operations internally; those are separate from the explicit
application `SELECT 1` above.

## Optional schema initialization

[Script](../Backend/scripts/init_db.py):

```python
from Backend.config.database import Base, engine
from Backend.models.student_model import Student

Base.metadata.create_all(bind=engine)
```

This operation is not part of admission fetching or normal request handling.
Running the script performs database schema writes when mapped tables are missing.
It was not run while preparing this documentation.

The [Student model](../Backend/models/student_model.py) registers `students`:

| Column | Model type / constraint |
|---|---|
| `id` | Integer primary key, indexed |
| `first_name` | String(255), non-null |
| `last_name` | String(255), non-null |
| `full_name` | String(255), non-null |
| `class_name` | String(100), non-null |
| `package` | String(100), non-null |
| `year` | String(20), non-null |

SQLAlchemy checks whether registered tables exist and generates MySQL DDL to
create missing tables and their indexes. There is no handwritten CREATE TABLE
query in the script; the exact DDL is generated from the model and SQL dialect.
`create_all()` is not a migration that updates the columns of an existing table.

The `students` table is distinct from `users`. This script does not create or
populate `users`, `users_schools` or `paid_users`, which must already exist for
retrieval features. The runtime retrieval queries documented here perform no
INSERT, UPDATE or DELETE operations. Mapping outputs and sessions are written
to files rather than these database tables.
