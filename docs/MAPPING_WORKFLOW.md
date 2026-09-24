# Student mapping workflow

The workspace maps school records to existing accounts in three explicit stages:
**Admission Number**, **Email**, and **Full Name + Class**. A stage runs only when
its mapping button is clicked; navigation, refresh, column selection, searching,
and pagination never run mapping automatically.

**Terminology:** `Matched` passed the current stage; `Review` (shown as **Review
students**) needs attention; `Not Matched` may continue to the next stage. A
**Preview screen** only displays/downloads a result group—it is not another
classification. Status cells include the reason, for example
`Matched — Email and first name match`.

For cookie, session-folder, `state.json`, snapshot, and React-cache details, see
[Session and data flow](SESSION_AND_DATA_FLOW.md). Implementation entry points
are in [CODE_FLOW.md](CODE_FLOW.md).

## Session and API startup

The browser sends the HTTP-only workflow cookie with `credentials: "include"`;
the session ID is never placed in API URLs.

| Request | Purpose |
|---|---|
| `GET /api/v1/mapping/session` | Restore the cookie's unexpired session and return its UI summary. |
| `POST /api/v1/mapping/session` | Create a session and set the cookie when GET finds no usable session. |
| `POST /api/v1/mapping/configuration-preview` | Validate draft selections without committing them. |

```mermaid
sequenceDiagram
    participant UI as React browser
    participant API as Python API
    participant Disk as Workflow session folder
    UI->>API: GET /mapping/session + cookie
    alt Session is valid
        API->>Disk: Read state.json and referenced .bin files
        API-->>UI: Workspace summary (not full student rows)
    else Missing, expired, or unusable session
        UI->>API: POST /mapping/session
        API->>Disk: Create state.json
        API-->>UI: Set cookie + empty workspace summary
    end
    UI->>API: Upload, fetch, map, preview, or download
    API->>Disk: Read current state/snapshots
    API->>Disk: Write changed snapshots, then atomically replace state.json
    API-->>UI: Updated summary or requested page/file
```

Email and final-stage source metadata is cached in React while its source,
worksheet, results, and relevant settings are unchanged. Failed requests are not
cached; refresh clears this memory cache. Admission results are required before
downstream stages. Changing the school file or admission dump invalidates them and
shows **First run admission mapping.** until Admission is rerun.

### Storage and input files

| Location | Responsibility |
|---|---|
| HTTP-only cookie | Carries the opaque workflow session ID. |
| Browser `sessionStorage` | Remembers UI choices such as search, columns, page, and page size for the tab. |
| Session `state.json` | Manifest of settings, metadata, and references to snapshots. |
| Session `.bin` files | Content-addressed bytes for CSV/XLSX inputs and generated workbooks. |
| React context cache | Avoids repeated metadata calls until a dependency changes or the page refreshes. |

School and Dump accept CSV/XLSX upload; local-path loading supports the same
formats only when `ALLOW_LOCAL_FILE_PATHS` is enabled. XLSX files expose worksheet
selection. Dump can alternatively be fetched from SQL by numeric school index.
SQL fetches select school students and attach admission numbers with a `LEFT JOIN`,
retaining students without paid records. See [selection and counts](#sql-dump-selection-and-counts).
For SQL dumps, missing cells become empty text and records that are completely
identical after normalization are stored once. A failed lookup preserves the
currently loaded dump and results; replacement occurs only after a successful fetch.
Replacing an input creates/reuses its content-hash snapshot and invalidates
dependent results; it never edits the original uploaded file.

`state.json` is the logical source of truth: it identifies which hash-named
`.bin` belongs to each input and result. Unchanged bytes reuse their snapshot;
changed bytes create a new hash and the manifest link moves to it. The old file
is then **delinked**, not immediately deleted. After 24 hours of inactivity, the
entire session folder removes the manifest plus linked and unlinked snapshots.

### SQL dump selection and counts

`Backend/repositories/admission_dump_service.py` implements the SQL fetch:

1. Validate a numeric school index and look up a nonempty school name in
   `users_schools`. An unknown school causes an error.
2. Select `users` with `user_edu_school = :school_index` and `user_type = '0'`.
   Non-student users and users with a NULL type are excluded.
3. `LEFT JOIN paid_users` on `user_id` to attach admission numbers. Students with
   no paid record remain with a blank admission number.
4. If a user has any valid admission number, keep their valid admission entries
   and exclude their missing entries. For this check, SQL NULL, empty text,
   spaces-only text and case-insensitive trimmed `null` are missing. If no valid
   admission exists, retain the missing entries instead.
5. SQL `DISTINCT` removes duplicate selected records. Convert SQL NULL cells to
   empty text and remove rows that then become completely identical. Identifiers
   stay text, including leading zeros. The validity check trims admission text;
   it does not rewrite the stored admission value.

| Paid records for one selected student | Dump result |
|---|---|
| No paid record | One row with a blank admission |
| `001` | One row with `001` |
| `002`, `002` | One row with `002` |
| NULL, empty text, `003` | One row with `003` |
| `004`, `005` | Two rows for the same student |
| NULL, empty text only | One row with a blank admission after normalization |
| NULL, empty text, spaces-only text, literal `null` | Can retain several rows because these values are not all normalized to empty text |

Multiple distinct admissions are retained; the fetch does not select a first or
latest paid record, combine admissions, or introduce a conflict flag.

The student population to compare against is:

```sql
SELECT COUNT(*)
FROM users
WHERE user_edu_school = :school_index
  AND user_type = '0';
```

Assuming `users.user_id` uniquely identifies each user, the dump's distinct
student count represents this population at fetch time. **Dump records** and the
fetch message count retained rows; **Students** counts distinct user IDs. Row
count can exceed student count when one user has multiple retained admissions
or different missing-value representations. Counting all users for the school
without the student-type filter is a different comparison.

These rules apply to SQL fetches. Uploaded CSV/XLSX dumps are not automatically
reconciled against the database. A saved dump is a snapshot; database changes do
not appear until another fetch. Existing saved dumps must be fetched again to
include students that the previous inner join omitted.
See [Snapshot linking, updates and cleanup](SESSION_AND_DATA_FLOW.md#3-snapshot-linking-updates-and-cleanup)
for examples and failure behavior.

## Pipeline and forwarding

```mermaid
flowchart LR
    S["School file"] --> A["Admission"]
    D["Admission dump"] --> A
    A --> AM["Matched"]
    A --> AR["Review"]
    A --> AN["Not Matched"]
    AN --> E["Email"]
    E --> EM["Matched"]
    E --> ER["Review"]
    E --> EN["Not Matched"]
    EN --> F["Full Name + Class"]
    AN -. "optional direct source" .-> F
    D --> F
    F --> FM["Matched"]
    F --> FR["Review"]
    F --> FN["Not Matched: unresolved"]
```

- Normally only the preceding stage's `Not Matched` rows continue. Matched and
  Review rows are not forwarded.
- Full Name + Class can use Admission misses directly. After Email this may
  reprocess rows already handled there; account reconciliation resolves conflicts.
- Review rows remain in their originating workbook. Read-only previews mean that
  corrections require input changes and a rerun.
- Final misses have no further automatic stage or account creation.

## 1. Admission Number mapping

Inputs are the selected school and admission-dump worksheets. Required school
admission/name and dump admission/username/first-name columns must exist. Reserved
result-column names in the school file are rejected.

Completely identical school rows are deduplicated first; the first copy is kept
and dropped copies are counted, not classified as Review.

| Condition, in order | Result |
|---|---|
| School admission is blank | Review |
| Nonblank admission repeats in retained school rows | Every occurrence → Review |
| School first name is missing | Review |
| No dump row has the admission | Not Matched |
| Multiple dump rows have it | Review; select no account |
| One dump row but first name is missing/different | Review |
| Names match but dump username is blank | Review |
| Unique admission, equal first name, username present | Matched; copy username/user ID, subject to uniqueness |

Admission numbers are trimmed text (`00123` differs from `123`). First names are
trimmed/lowercased, and the web workflow compares the whole selected cell. Only
the CLI's optional `--full-name-column` extracts the first word. Dump evidence
counts the header as row 1. A nonblank user ID is not required.

Thus blank admissions and missing school first names are Review. Admission Not
Matched specifically means a unique, nonblank admission with a present school
first name was absent from the dump.

## 2. Email mapping

Email starts from current Admission `not_matched.xlsx`, removes Admission audit
columns, and needs at least one row. A separate SQL lookup fetches the selected
emails across all schools; it neither uses nor replaces the admission dump and
needs no school confirmation. Requested emails and identical returned rows are
deduplicated.

| Condition, in order | Result |
|---|---|
| Email blank after trimming | Not Matched — `Email missing` |
| Normalized email repeats in input | Every occurrence → Review, even if SQL found none |
| Multiple fetched records own email | Review; select no account |
| One candidate and first names match with more than one character | Matched, subject to school and account uniqueness checks |
| One candidate and matching first name is only one character (ignoring periods) | Review — `First name matches but is only 1 character` |
| One candidate but a first name is missing/different | Review; retain account evidence |
| Unique nonblank input email has no candidate | Not Matched — `Email not found` |

Emails and first names are trimmed and lowercased. The selected school first-name
column is compared directly with dump `user_firstname`; there is no fuzzy or
full-name comparison in Pass 1. Matching one-character names, including initials
such as `A.`, remain in Review. A successful name match must also pass the school
and account-uniqueness checks. Email misses normally continue, and the lookup is
saved as `email_dump.csv`.

Pass 2 retries only Review rows whose email was found but whose first name was
different. The user selects a separate school full-name column. Pass 2 compares
its sorted characters with dump `fullname` (falling back to first name plus last
name), ignoring case and whitespace. The school and account checks still apply.

## 3. Full Name + Class mapping

This uses Admission or Email misses plus the saved admission dump—not the email
dump. Required source/dump columns must exist. Dump rows remain eligible when
their admission number is blank; matching is based on name and class in this
stage. Neither round runs automatically.

### Round 1: concatenated key

The source key is lowercased, trimmed full name with literal spaces removed plus
trimmed/lowercased Class Number: `Alice Smith` + `3` → `alicesmith3`. It is
compared with dump `generated_col`.

| Condition | Result |
|---|---|
| Source name or class missing | Not Matched with specific reason |
| Key occurs multiple times in dump | Review |
| Key occurs once | Matched; copy username/user ID, subject to uniqueness |
| Key absent | Not Matched |

SQL `generated_col` uses name plus package-adjusted class: package **14** uses
`user_edu_class`, **12** adds 1, **11** adds 2, and others use stored class.
Uploaded dumps must provide a compatible column. Round 1 does not numerically
normalize source class (`3` differs from `3.0`); dump-browser display offsets are
separate from this rule.

### Round 2: sorted characters and class

Round 2 retries only Round 1 misses using selected dump name/class columns. Names
are lowercased, all whitespace removed, and **characters** sorted; counts,
punctuation, and accents remain significant (`Mary Ann` matches `Myra Nan`).
Original exported names are unchanged.

Sorted names and classes must match. Integral classes `04`, `4`, and `4.0` are
equal. For dump `user_edu_class`, add 1 (stored `3` matches source `4`); other
class columns compare directly. Round 2 ignores `generated_col` package rules.

One candidate is Matched, none/missing data is Not Matched, and multiple candidates
are Review. Round 1 Matched/Review rows remain. Round 2 replaces its previous
retry results from saved Round 1 misses, including after session restore; rerunning
Round 1 resets Round 2. It adds no export names or database writes.

## Account uniqueness and reconciliation

Each stage rejects a shared nonblank **username OR user ID** among candidate
matches. Identifiers are trimmed, case-sensitive text; blanks are ignored. Every
row sharing either identifier moves to Review with evidence retained.

After Email/final runs and when entering those pages, the backend reconciles saved
matches across stages. No stage has priority: conflicting Admission and Email
matches both become Review. Duplicate-account Review rows continue reserving their
identifiers; ordinary Review rows caused by name/lookup ambiguity do not.
Reconciliation changes Matched/Review workbooks, never Not Matched input. This is
workspace-level, not a database-wide registration constraint.

## Results, previews, and invalidation

| Stage | Matched | Review | Not Matched / next input |
|---|---|---|---|
| Admission | `matched.xlsx` | `review.xlsx` | `not_matched.xlsx` → Email/direct final |
| Email | `email_matched.xlsx` | `email_review.xlsx` | `email_not_matched.xlsx` → final |
| Full Name + Class | `full_name_class_matched.xlsx` | `full_name_class_review.xlsx` | `full_name_class_not_matched.xlsx` → unresolved |

Every run writes three XLSX files, with headers even when empty. They contain
school fields, evidence, account fields, and status/reason. Admission audit fields
are removed downstream; final results sourced from Email misses retain Email
evidence. No combined master workbook is produced.

Result previews paginate and download Excel/CSV (UTF-8 BOM):
`GET /api/v1/mapping/result-previews/{stage}/{filename}?page=1&limit=50`.
They are read-only; the former Admission move API returns HTTP 403.

Invalidation follows dependencies:

- School/dump, worksheet, or Admission-column changes invalidate Admission;
  rerunning Admission clears later results.
- Email-column changes clear its dump/results and final results; rerunning Email
  clears final results.
- Final source or name/class changes clear final results.
- Mapping/reconciliation rebuild only affected workbooks.

Original uploads remain separate. SQL admission fetch saves
`school_<index>_dump.csv`; Email saves `email_dump.csv`.

## School and dump browsing: data and pagination

Shared frontend `FileViewer` requests only the displayed student page:

| Page | API |
|---|---|
| School | `GET /api/v1/mapping/table-previews/school` |
| Dump | `GET /api/v1/mapping/table-previews/dump` |

`fileApi.table` sends the cookie and optional parameters:

| Parameter | Meaning |
|---|---|
| `page`, `limit` | One-based page and size; UI offers 25/50/100, default 50. |
| `sheet` | Selected Excel worksheet. |
| `query` | Case-insensitive literal search (not regex). |
| `columns` | Repeated selected search columns; omitted means all. Multiple use OR. |
| `class_column`, `section_column` | School-only statistics columns. |

```text
GET /api/v1/mapping/table-previews/school?page=2&limit=25&query=alice&columns=FIRST%20NAME&columns=Email
```

Opening a viewer or changing page, size, sheet, search, columns, or statistics
columns requests data. Filter/size changes reset page 1. `AbortController`
cancels obsolete requests; the current request shows `Reading file...`.

Backend `table_view` in
`Backend/routes/file_workflow_routes/source_files_preview.py` validates the
cookie/session and columns, reads the saved snapshot/worksheet, filters the full
DataFrame, clamps the page, and returns only that slice. Response fields are
`columns`, current-page `rows`, unfiltered `total`, filtered `found`, `page`,
`pages`, `offset`, and `end`. Dump also returns overview, distinct student count,
inferred school index, and `generated_col` availability; School returns its
class/section overview when configured.

The `.bin` used here is the saved School/Dump source, not a search cache. Search
results are temporary and create no snapshot.

Statistics use the full saved source, but only the current student page crosses
HTTP. Browsing/searching never changes files or reruns mapping.

## Production reference

### Main API surface

All workflow routes below require the session cookie except session creation and
the health check.

| Method and path | Responsibility |
|---|---|
| `GET /` or `GET /api/v1/mapping/health` | Service health response. |
| `POST /api/v1/mapping/files/{school|dump}` | Upload CSV/XLSX input. |
| `POST /api/v1/mapping/files/{kind}/path` | Load an allowed server-local CSV/XLSX path. |
| `POST /api/v1/mapping/student-dump/fetch` | Fetch school dump from SQL. |
| `POST .../admission-mapping/run` | Run Admission pass 1. |
| `POST .../admission-mapping/second-pass` | Run Admission pass 2. |
| `POST .../email-mapping/run` / `second-pass` | Run Email pass 1/2. |
| `POST .../full-name-class-mapping/run` | Run selected final round. |
| `GET .../table-previews/{kind}` | Read paginated source data. |
| `GET .../result-previews/{stage}/{filename}` | Read paginated results. |
| `GET .../downloads/{kind}` | Download source/result as supported CSV/XLSX. |

`...` means `/api/v1/mapping`. Request and response models remain authoritative
in the FastAPI/OpenAPI schema.

## How workflow snapshot storage works

### 1. Creating a `.bin` snapshot

When the backend saves a source file or generated workbook:

```text
File bytes
    ↓
Calculate SHA-256 hash
    ↓
Use hash as filename
    ↓
<hash>.bin
```

Example:

```text
school.csv bytes
    ↓
SHA-256: a4cc240411d6...
    ↓
a4cc240411d6....bin
```

The `.bin` file contains the original bytes:

- Uploaded CSV bytes
- Uploaded XLSX bytes
- SQL-generated CSV bytes
- Generated result-workbook bytes

The `.bin` extension does not mean the data was converted into a custom format.

### 2. Linking from `state.json`

`state.json` stores metadata and the snapshot filename:

```json
{
  "saved_admission_school": {
    "metadata": {
      "name": "school.csv",
      "source": "school.csv"
    },
    "file": "a4cc240411d6....bin"
  }
}
```

Conceptually:

```text
state.json
    │
    ├── saved_admission_school
    │        └── school-hash.bin
    │
    ├── saved_admission_dump
    │        └── dump-hash.bin
    │
    └── admission_exports
             ├── matched.xlsx     → matched-hash.bin
             ├── review.xlsx      → review-hash.bin
             └── not_matched.xlsx → unmatched-hash.bin
```

`state.json` gives meaning to each `.bin` file. Without the manifest, the hash filename alone does not indicate whether it contains a school file, Dump, or result workbook.

### 3. Updating a file

When the bytes change:

```text
Old bytes → old hash → old-hash.bin
New bytes → new hash → new-hash.bin
```

The backend:

1. Writes the new `.bin` snapshot.
2. Updates `state.json` to point to it.
3. Atomically publishes the new `state.json`.

```text
Before:
state.json → old-hash.bin

After:
state.json → new-hash.bin
```

If the bytes are unchanged, the hash is unchanged, so the existing `.bin` file is reused.

### 4. Updating one result group

The entire session folder is not replaced.

For example, if only `matched.xlsx` changes:

```text
Before:
matched.xlsx     → hash-A.bin
review.xlsx      → hash-B.bin
not_matched.xlsx → hash-C.bin

After:
matched.xlsx     → hash-D.bin
review.xlsx      → hash-B.bin
not_matched.xlsx → hash-C.bin
```

Unchanged result bytes keep the same hash reference.

### 5. Delinking a file

A `.bin` file becomes delinked when its reference is removed from `state.json`.

For example, rerunning Admission clears Email results:

```text
Before:
state.json
  ├── admission_exports
  └── email_exports → email-result.bin

After:
state.json
  └── admission_exports
```

The Email result `.bin` still may physically exist, but it is no longer accessible through the workflow because `state.json` no longer references it.

This is an important distinction:

```
Delinked ≠ immediately deleted
```

> [!IMPORTANT]
> The application currently deletes the entire workflow folder after 24 hours of inactivity, which removes `state.json` and all its `.bin` files.
>
> However, based on the current storage implementation, individual unreferenced `.bin` files are not immediately garbage-collected when they become delinked. They remain until the session expires and the complete folder is deleted.
>
> Therefore, the documentation should not claim that old `.bin` files are deleted immediately after replacement.

### 6. Loading a snapshot

When the backend needs a source or result:

```text
Read state.json
      ↓
Find logical entry
      ↓
Read referenced hash.bin
      ↓
Restore original filename and metadata
      ↓
Parse CSV/XLSX or return workbook bytes
```

If the `.bin` reference is missing or invalid, the backend now returns `409 Conflict`.

### 7. Session expiry

After 24 hours of inactivity:

```text
workflow_sessions/<session-id>/
    ├── state.json
    ├── source-hash.bin
    ├── dump-hash.bin
    └── result-hash.bin
              ↓
       Entire folder deleted
```
