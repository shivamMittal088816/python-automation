# Bulk registration conversion

Open `/bulk-reg` on the frontend. This service is independent of mapping state.
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

These values override input values on every row:

| Column | Value |
|---|---|
| SCHOOL | School name fetched from the database |
| School Number | Entered school index |
| user_subscription_date | 2026-04-01 00:00:00 |
| user_package | 14 |
| user_activated | 1 |
| user_subscribed | 1 |
| year | 2026 |

Other input values are preserved; missing columns remain blank. Name, class,
gender, and other derivation rules have not yet been defined. Rows are not
deduplicated. Identifiers stored as text retain leading zeros. Preview shows the
first 20 rows; exports include every row. No registrations are submitted.

The verified index and fetched name override school values in every input row.
Changing the index clears verification, fetched name, preview, and downloads.
A working database is required, but mapping state is not used. Conversion and
download recheck school identity in the database and read the original upload or
local path again; preview a changed local file again to review its latest contents.

API endpoints (under the configured API prefix, normally `/api/v1`):

- `POST /bulk-reg/files`: input preview from multipart `file` and optional `sheet`.
- `POST /bulk-reg/files/path`: input preview from JSON `path` and optional `sheet`.
- `GET /bulk-reg/schools/{school_index}`: verify index and fetch school name.
- `POST /bulk-reg/convert`: multipart `school_index`, `file_format` (`preview`,
  `csv`, or `xlsx`), optional `sheet`, and exactly one of `file` or `path`.

Local paths require `ALLOW_LOCAL_FILE_PATHS=true`.

## Cross-tab workspace

Bulk registration has its own browser workspace, separate from mapping. Tabs in
the same browser profile using the same origin share school index, verification,
file path, uploaded file, input preview, and output preview. IndexedDB stores the
uploaded file itself, so a newly opened or reloaded tab can generate and download
output without selecting the file again. Downloads occur only in the requesting
tab. Busy indicators and errors are local to each tab.

BroadcastChannel announces changes; storage events and focus refresh provide
fallback updates. Only revision notifications go through localStorage. Atomic
IndexedDB revision checks reject delayed API results when another tab has already
changed the workspace. No mapping session or mapping API is used.

The workspace persists after leaving the page or closing tabs. **Clear file**
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
