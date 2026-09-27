# Bulk registration conversion

Open `/bulk-reg` on the frontend. This service is independent of mapping state.
Its input and generated output files are stored as content-addressed `.bin`
snapshots under a dedicated bulk-registration workspace. Each workspace has a
`state.json` manifest linking the original filename, selected worksheet, school,
row count, and generated formats to those snapshots.
For startup commands, see [Run the project](RUNNING.md).

1. Enter the **School index** and select **Verify school index**. The service
   checks `users_schools.school_id` and retrieves `school`. On success it shows
   **School index verified** and a read-only **School name fetched** field.
   A missing index, unavailable database, or missing school name blocks conversion.
2. Upload or drop a CSV/XLSX file, or load a path on the backend computer.
   For XLSX, select **Working sheet** to choose the workbook tab. The first sheet
   is selected initially, including when it is empty, so another tab can be chosen.
   Input preview uses the selected sheet. Changing sheets synchronizes the selection
   across tabs but keeps the previous output. Only a successful **Generate preview**
   replaces that output in every tab; failed runs retain the previous results.
   Downloads use the worksheet that produced the displayed output, even if another
   sheet has since been selected. The output heading identifies its worksheet.
   CSV files have no worksheet selector. Empty sheets cannot be converted.
3. Select **Generate preview**, then **Download XLSX** or **Download CSV**.

The input headers must be a subset of these exact, case-sensitive headers. Every
download has all 24 headers in this order:

```text
FIRST NAME, LAST NAME, FULL NAME, Class Number, CLASS, Section, EMAIL,
PASSWORD, CONTACT, GENDER, Gender Number, Category, USER TYPE, SCHOOL,
School Number, user_subscription_date, user_package, user_activated,
user_subscribed, user_name, admission_number, house, section_index, year
```

Every output row receives the same Excel formula in `PASSWORD`:

```excel
=(RANDBETWEEN(1,9))&(RANDBETWEEN(0,9))&RANDBETWEEN(0,9)&RANDBETWEEN(0,9)&RANDBETWEEN(0,9)&RANDBETWEEN(1,9)
```

The password formula's digit rules are calculated once by the backend when the
preview is generated. That final six-digit value is stored in the authoritative
converted-output snapshot and reused as literal text by the preview, CSV, and
XLSX downloads, so a student's password remains identical in every format.

These values override input values on every row:

| Column | Value |
|---|---|
| Category | 0 |
| USER TYPE | Student |
| SCHOOL | School name fetched from the database |
| School Number | Entered school index |
| user_subscription_date | 2026-04-01 00:00:00 |
| user_package | 14 |
| user_activated | 1 |
| user_subscribed | 1 |
| year | 2026 |

Other input values are preserved; missing columns remain blank. `Gender Number`
is derived from `GENDER` (`Male` = 1, `Female` = 2, `Others` = 3). Rows are not
deduplicated. Identifiers stored as text retain leading zeros. Output preview is
paginated at 20 rows per page; exports include every row. No registrations are submitted.

`CLASS` is derived from the class name in `Class Number`: Class I-XII map to 0-11, followed by
Other = 12, Nursery = 13, LKG = 14, UKG = 15, Passed Out = 16, KG = 17,
Pre Nursery = 18, Pre Primary = 19, Pre School = 20, and Play Group = 21.

Every distinct nonblank `Section` is checked against `users_sections.section`.
Matching ignores capitalization, repeated spaces, and surrounding spaces. A match
writes its `section_id` into `section_index`. The preview lists missing sections in
a warning table so they can be inserted into `users_sections`; their
`section_index` remains blank until the database contains them.

The verified index and fetched name override school values in every input row.
Changing the index clears verification, fetched name, preview, and downloads.
A working database is required, but mapping state is not used. Conversion and
download recheck school identity in the database and read the original upload or
local path again; preview a changed local file again to review its latest contents.

API endpoints (under the configured API prefix, normally `/api/v1`):

- `GET /bulk-reg/workspace`: read the cookie-selected workspace. Missing or
  expired workspaces return HTTP 409 without changing the cookie.
- `POST /bulk-reg/workspace`: initialize or restore the cookie-selected workspace
  and return its complete browser-safe summary. The browser serializes this
  operation with reset and rechecks the current cookie before initializing.
- `POST /bulk-reg/files`: input preview from multipart `file` and optional `sheet`.
- `POST /bulk-reg/files/path`: input preview from JSON `path` and optional `sheet`.
- `POST /bulk-reg/files/stored`: change the selected worksheet of the saved input.
- `POST /bulk-reg/school`: verify and save a school index.
- `GET /bulk-reg/schools/{school_index}`: verify index and fetch school name.
- `POST /bulk-reg/convert`: multipart `school_index`, `file_format`
  (`preview`, `csv`, or `xlsx`), optional `sheet`, and preview `page`.
- `DELETE /bulk-reg/file`: clear input/output references while retaining the workspace.
- `DELETE /bulk-reg/workspace`: explicitly reset and replace the whole workspace.

Every mutation except initialization requires `X-Workspace-Revision`.
A stale revision returns HTTP 409. Delayed reads and mutations cannot create a
replacement workspace; only explicit initialization or reset can set its cookie.
Complete workspace operations, including snapshot reads, are serialized within
the single-worker server so concurrent requests cannot commit the same revision.

Local paths require `ALLOW_LOCAL_FILE_PATHS=true`.

## Cross-tab workspace

Bulk registration has its own backend workspace, separate from mapping. An
HTTP-only cookie identifies it. React keeps only the current in-memory API summary;
neither localStorage nor IndexedDB is used. On refresh, React fetches the complete
summary from `GET /bulk-reg/workspace`. The backend `.bin` snapshot is reused
for page requests and downloads. Downloads occur only in the requesting tab.
Busy indicators and errors are local to each tab.
Unsubmitted school-index and path edits are also local to each tab. Focus refresh
preserves those drafts; successful verification or file loading commits the
corresponding field. Reload discards drafts, and a workspace reset clears them.

BroadcastChannel announces successful state replacement and focus refresh is the
fallback. Backend revision checks reject delayed API results when another tab has
already changed the workspace. The browser also rejects older responses and
responses from a workspace that has since been reset. No mapping session or
mapping API is used.

Bulk workspaces expire after 24 hours without API activity. Valid workspace reads
refresh the activity timestamp. Expiry removes `state.json` and every referenced
`.bin` file; the next request creates a new empty workspace. Before expiry, the
workspace persists after leaving the page or closing tabs. **Clear file**
opens a confirmation overlay; **Confirm** removes the source and output across
tabs, while **Cancel** or Escape leaves them unchanged. **Reset bulk registration** clears the
whole bulk workspace across tabs. Browser site-data deletion also clears it.
Different browsers, profiles, hostnames, or ports do not share this workspace.
Site storage must be available; storage errors are displayed rather than silently
continuing with an unsaved workspace.

## Frontend organization

`BulkRegistrationPage.jsx` composes the layout. `useBulkRegistration.js` owns
file loading, school verification, worksheet changes, conversion, and downloads.
The `components/` folder contains `SchoolVerification`, `RegistrationFileInput`,
`RegistrationDefaults`, `RegistrationActions`, and `RegistrationPreviews`.
`useBulkRegistrationWorkspace.js` remains responsible for persistence and tab sync.
