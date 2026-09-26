# React UI refinement

Current startup commands for the updated folders: [Run the project](../../backend/docs/RUNNING.md).

## Follow-up: explicit mapping actions

Page navigation actions now use a shared `ActionLink` with button styling, including Search dump, Back to mapping, overview, Preview screen, and stage navigation. Their link semantics and destinations remain unchanged.

The three stages now display Start admission mapping, Start email mapping, and Start full name mapping. Automatic duplicate-reconciliation requests on entering Email and Full Name pages were removed; backend duplicate checks during mapping remain unchanged. Existing results are explicitly labeled as saved results, and opening a page does not initiate a new mapping run. No backend code changed.

A browser regression test records mapping and reconciliation requests and verifies that only explicit Start clicks trigger mapping, including after navigating and reloading all three stages. Existing workflow selectors were updated for the new button labels.

Follow-up verification: production build passed; all 6 browser tests passed using the alternate-port configuration. The updated Preview screen screenshot was inspected to confirm button styling.

Visual and presentation changes only. The existing seven routes, API calls, form values, validation, mapping algorithms, result classifications, downloads, workflow order, and workspace persistence remain unchanged. No backend, service, hook, context, or router files were edited for this task.

## Files changed

- `src/index.css`: global typography, focus states, inputs, and shared spacing.
- `src/components/layout/AppLayout.jsx`: navigation hierarchy, icons, active states, responsive shell, and bounded page width.
- `src/components/common/Controls.jsx`: shared buttons, alerts, fields, cards, metrics, and loading indicators.
- `src/components/common/FileInput.jsx`: upload area, segmented source selector, and loaded-file feedback.
- `src/components/common/FileViewer.jsx`: consistent headers, useful empty states, loaded-file feedback, and action emphasis for all three file pages.
- `src/components/common/SchoolIdentity.jsx`: school context styling.
- `src/components/tables/DataTable.jsx`: sticky headers, lighter row separators, hover styling, scroll containment, and semantic column headers.
- `src/pages/AdmissionMapping/AdmissionMappingForm.jsx`: workflow stepper, coordinated input cards, source options, mapping section hierarchy, and result badges.
- `src/pages/AdmissionPreview/AdmissionPreviewPage.jsx`: page header and a prominent existing continuation link.
- `src/pages/EmailMapping/EmailMappingPage.jsx`: page header.
- `src/pages/EmailMapping/EmailForm.jsx`: mapping section header and shared form presentation.
- `src/pages/FullNameClassMapping/FullNameClassMappingPage.jsx`: page header, selected source styling, clearer section descriptions, and responsive settings.

## New files and reusable components

`src/components/common/Presentation.jsx` contains `Icon`, `PageHeader`, `SectionHeader`, `Stepper`, `LoadedFile`, `EmptyState`, and `Badge`. Existing shared controls were extended rather than replaced with a UI framework.

`e2e/presentation.spec.js` adds browser coverage for all seven active pages at 1440, 820, and 390 pixels, page overflow, long filenames, runtime errors, and screenshot capture of empty, loading, error, configured, and result states. The original workflow tests remain unchanged.

## Design system

- Colors: slate page background, white surfaces, dark slate text, blue primary actions; subtle green, amber, and red status badges.
- Typography: existing system sans-serif, 24px page titles, restrained section headings, readable 14px controls and body copy.
- Spacing: 24px page section rhythm, responsive page padding, 20–24px card padding, and bounded main content.
- Cards: subtle slate borders, rounded corners, and small shadows.
- Buttons: primary blue, secondary white, with reusable ghost and danger variants; visible focus and disabled states.
- Status: textual labels plus color; loaded files include a check icon, alerts include an icon, loading includes a spinner with reduced-motion support.
- Styling: Tailwind utilities remain the primary system. No dependencies were added.

## Page inspection

| Page | Improvement |
| --- | --- |
| Admission Mapping | Stateful stepper, upload areas, segmented controls, selectable dump-source cards, constrained settings, and result badges. |
| Admission Preview screen | Consistent header, status metrics, stronger email continuation action, readable tables and pagination. |
| School File | Loaded-file status, useful empty state, clearer overview/search cards, consistent table styling. |
| Dump File | Shared header and empty state, prominent save action, school metrics, consistent search and tables. |
| Email Mapping | Clear page purpose and settings section, shared feedback, buttons, result metrics and tables. |
| Email Dump | Consistent source context, search controls, file status, and table presentation. |
| Full Name + Class | Clear input selection, highlighted selected source, simpler settings description, responsive controls and shared results. |

Jobs and Review students pages had already been removed from the current React implementation. Their existing redirects and API unavailability are preserved. Manual transfers were already unavailable and remain unavailable. No new routes or workflow stages were introduced.

Click-to-select upload behavior is preserved; the upload area does not promise drag and drop. No sticky action bar was added because the current actions remain visible within their sections without duplication.

## Verification

- Production build: `npm run build` passed (63 modules transformed).
- Browser suite: `npm.cmd test -- --config=playwright.feature-removal.config.js` passed: 5 tests in 58 seconds (4 original workflow tests and 1 new presentation test).
- The alternate existing configuration uses port 5174 because the local application already occupies 5173.
- The suite uses the actual FastAPI services with isolated fixture repositories and storage; SQL fetching is verified through the fixture repository, not a live production database.
- Existing tests exercise uploads, paths, dump fetch, admission/email/full-name mapping, downloads, locked Preview screens, filters, reload restoration, and removed routes.
- Rendered screenshots were inspected for admission, Preview screen, school, dump, email mapping, email dump, full-name mapping, long filenames, empty and error states, and responsive layouts.
- Screenshots are generated in `test-results/` and can be regenerated with the browser command above.
