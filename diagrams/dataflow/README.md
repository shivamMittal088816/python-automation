# Detailed student-mapping data flow

[Open the diagram](output/dataflow.html) · [Editable Archify source](specs/dataflow.json)

The current diagram has 75 nodes and 60 labeled flows across 15 numbered paths.
It follows the current repository's data objects, HTTP boundaries, transformations,
classification rules, result snapshots, previews, and downloads.

## Read and navigate

Read each numbered path left to right. Repeated named snapshots are references to
the same session data; they are not extra databases. References such as “lane 04”
connect decomposed paths without long wires across unrelated operations. Archify
route tracing follows drawn arrows within a path; it cannot traverse a textual
reference between paths.

The authored canvas is 1080 × 3320. Vertical page scrolling is intentional.
Use the five guided views, Node Finder, focus, and built-in pan/zoom to explore it.
The installed viewer reveals fine-detail tags at 175% zoom or through node focus.
Its typography has not been modified. No custom viewer, clipping, or application
route was added.

The installed Data Flow renderer uses five fixed columns and five base rows.
Supported `yOffset` positions extend the diagram vertically. This source uses
Archify's `standard` profile for the requested dense map.

## Repository evidence

All paths below are relative to the repository root.

| Diagram paths | Primary implementation evidence |
| --- | --- |
| 01 Upload / HTTP / session | `frontend/src/components/common/FileInput.jsx`; `frontend/src/services/fileApi.js`; `frontend/src/services/api.js`; `backend/app/routes/file_workflow_routes/file_inputs.py`; `backend/app/api/session_cookie.py` |
| 02 Workbook reading / configuration | `backend/app/api/file_workflow_snapshots.py`; `backend/app/api/file_workflow_configuration.py`; `backend/app/services/admission_mapping/admission_file_reader.py` |
| 03 SQL school reference | `backend/app/repositories/admission_dump_service.py`; `backend/app/routes/file_workflow_routes/file_inputs.py` |
| 04–05 Admission | `backend/app/routes/file_workflow_routes/admission_mapping.py`; `backend/app/services/admission_mapping/admission_mapping_pipeline.py`, `admission_dump_lookup.py`, `admission_name_comparison.py`, `admission_row_classification.py`, `admission_duplicate_checks.py`, `admission_result_exports.py`, `admission_workbook.py` |
| 06–08 Email | `backend/app/routes/file_workflow_routes/email_mapping.py`; `backend/app/repositories/email_dump_service.py`; `backend/app/services/email_mapping/email_input.py`, `email_mapping_pipeline.py`, `email_dump_lookup.py`, `email_row_classification.py`, `email_result_exports.py` |
| 09–10 Full Name + Class | `backend/app/routes/file_workflow_routes/full_name_class_mapping.py`; `backend/app/services/full_name_class_mapping/full_name_class_mapping_pipeline.py`, `full_name_class_dump_lookup.py`, `full_name_class_row_classification.py`, `full_name_class_result_exports.py` |
| 11 Persistence | `backend/app/api/file_workflow_state.py`; `backend/app/api/file_workflow_session_storage.py`; `backend/app/utils/file_snapshots.py` |
| 12 Review previews | `backend/app/routes/file_workflow_routes/mapping_preview_results.py`; `backend/app/api/file_workflow_responses.py`; `frontend/src/components/common/ResultPreview.jsx` |
| 13 Group downloads | `backend/app/routes/file_workflow_routes/file_downloads.py`; `frontend/src/services/fileApi.js` |
| 14 Final workbook | `backend/app/services/final_results_workbook.py`; `backend/app/routes/file_workflow_routes/file_downloads.py` |
| 15 Local files / invalidation | `backend/app/routes/file_workflow_routes/file_inputs.py`; `backend/app/api/file_workflow_invalidation.py`; `backend/app/services/email_mapping/email_input.py` |

## Data objects and boundaries

- Upload: browser File → FormData → FastAPI UploadFile → snapshot dictionary.
  An enabled local-path request reads bytes on the backend computer.
- Snapshot: name, bytes, source and optional path/school metadata. Disk storage is
  `backend/storage/temp/workflow_sessions/<session UUID>/`, with SHA-256-named
  `.bin` files and a `state.json` manifest.
- Session: cookie identifies the workspace; mutations include
  `X-Workspace-Revision`. A lock serializes workspace access; stale revisions
  return 409. Session inactivity expiry is 24 hours, distinct from the cookie's
  72-hour maximum age.
- Parsing: Excel worksheet names and selected sheet feed a temporary CSV/XLSX
  file. pandas reads strings and preserves leading zeros. The temporary file is
  deleted after parsing.
- Configuration: selected school/dump worksheets, school admission/name columns,
  detected dump aliases and committed run signatures. Configuration-preview uses
  a copied state; selecting draft fields alone does not commit a new mapping.
- Results: each stage stores three independent XLSX byte snapshots and row counts.
  Status and reason accompany original school data and stage-specific audit fields.
- UI summary: file metadata and hashes, selected settings, export counts and
  versions, and committed run-column details return as JSON.

## Matching and lineage

Admission removes exact duplicate school rows, indexes trimmed admission strings,
compares lowercased first-name cells and applies duplicate review rules. The current
endpoint passes `name_is_full=False`.

Email can read the school worksheet or Admission's `not_matched.xlsx`. Its SQL
lookup runs across schools in batches of 500 unique normalized email values; the
classification stage then checks the matched account's school. The endpoint does
not invoke the optional sorted-full-name comparison branch.

Full Name + Class can read the school worksheet, Admission misses or Email misses.
It compares the normalized name/class concatenation to all reference
`generated_col` candidates. The detailed rule cards in the HTML show missing,
duplicate, mismatch and successful-match outcomes for all three stages.

Saved Review groups are classification outputs. The current UI supports inspection
and download, with no manual group-transfer action. The preview endpoint's legacy
cleanup/enrichment operates on display data and does not persist reclassification.

## Exact export behavior

The combined workbook uses the fixed `FINAL_RESULT_SHEETS` list:

| Stage | Included sheets |
| --- | --- |
| Admission | Admission Matched; Admission Review; Admission Not Matched |
| Email | Email Matched; Email Review |
| Full Name + Class | Class Matched; Class Review; Final Not Matched |

Only available saved groups are included. Email Not Matched is individually
downloadable but omitted from the combined workbook. Assembly preserves independent
schemas; it does not reconcile or deduplicate students across stages.

Group CSV uses UTF-8 with BOM. SQL dump snapshots use UTF-8 CSV. XLSX writers keep
formula-like input values as literal text.

## Regenerate

Run from `D:\python-api`:

```powershell
.\archify.ps1 validate dataflow diagrams\dataflow\specs\dataflow.json --quality standard --json
if ($LASTEXITCODE -ne 0) { throw 'Data-flow validation failed' }
.\archify.ps1 deliver dataflow diagrams\dataflow\specs\dataflow.json diagrams\dataflow\output\dataflow.html --quality standard --json
if ($LASTEXITCODE -ne 0) { throw 'Data-flow delivery failed' }
.\archify.ps1 visual-check diagrams\dataflow\output\dataflow.html --json
```

The stock visual-check command requires one-screen desktop containment. Its
overflow failure is expected for this explicitly requested scrolling canvas;
review its other diagnostics separately. Do not compress the graph to remove
intentional vertical scrolling.

Open:

```powershell
Start-Process "D:\python-api\diagrams\dataflow\output\dataflow.html"
```

## Verification

Final deterministic delivery: 9/9 checks, standard profile, zero errors/warnings,
zero crossings, zero ambiguous corridors, and no label/route clearance issues.
See [delivery receipt](output/dataflow.delivery.json).

The browser receipt and screenshots in `output/dataflow.visual-check.*` bind to
the preceding artifact (SHA-256 beginning `68ba6356`). They passed readability,
horizontal containment and viewer-chrome checks at all four desktop sizes.
Their only diagnostics are the intentionally permitted vertical overflow.
Light/dark screenshots of the upper paths were visually inspected.

The final artifact adds classification/export notes and corrects one endpoint tag.
Its deterministic checks passed again. Interactive local-file inspection was
blocked by the browser tool's URL policy, so final-artifact browser testing and
full-canvas perceptual review are not claimed. The supplementary
[review record](output/dataflow.review.json) preserves this distinction.

No application code or runtime routes were changed. Bulk registration is outside
this mapping data-flow scope.
