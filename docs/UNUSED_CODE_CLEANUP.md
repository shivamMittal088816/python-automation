# Unused code cleanup

Removed code with no active application callers:

- Retired `Backend/api/file_workflow_storage.py` school snapshots, staging,
  rollback and restore. Existing stored school files are untouched.
- `Backend/repositories/user_package_repository.py`.
- Unused `find_by_email`, `find_by_admission_number` and
  `find_name_candidates` methods from `UserStudentRepository`. Its active
  student browsing query is unchanged.
- `Backend/utils/api_responses.py` and the unused `ApiResponseDTO.error` method.
- The unused `useRequest.reload` callback and its revision state.
- The unused workspace-context `refresh` callback and exposed `setNotice` value.
- The retired `web` directory entry in a test's Python import path.

Storage regression tests now use session persistence instead of the retired
school-storage implementation. The browser fixture no longer configures it.
Documentation describes the current session-only behavior.

Retained framework-discovered routes, Pydantic configuration, ORM registration,
public service facades, CLI entry points, active dependencies and test fixtures.
The unused tuple binding inside admission classification was retained with the
rest of that mapping implementation. Runtime files and logs were not deleted.

## Initial cleanup verification

- All Python mapping-service source files match their pre-cleanup SHA-256 hashes.
- The complete OpenAPI schema matches the pre-cleanup schema.
- No missing backend import paths or unused frontend imports were found.
- Frontend production build passes.
- Browser suite: 4 passed, 5 failed out of 9. All five failures look for
  `Start admission mapping`; the admission form now renders `Run mapping`.
  Passing checks cover draft-column behavior, session navigation, removed routes,
  and file-path/SQL-loading/error/responsive navigation behavior. The stale
  browser selectors were not changed as part of this unused-code cleanup.
- Backend suite: 117 passed, 2 failed out of 119. Both failures reproduce when
  run alone against unchanged mapping services:
  - `test_other_review_reasons_and_nonunique_admissions_are_excluded`: expects
    6 Review students, receives 5.
  - `test_user_id_duplicates_go_to_review_in_every_stage`: expects 2 Review students, receives 0.

Mapping rules and those assertions were not changed to force passing tests.

## Follow-up regression test corrections

The backend fixtures now reflect the existing rules: a blank admission number
stays in Not Matched, and duplicate-account fixtures supply valid admission
numbers and matching school identities. Assertions verify unchanged pass-two
workbooks and the actual duplicate-account Review students reason, rather than only counts.
All 119 backend tests pass.

Browser tests use the current single-pass Run mapping buttons, save school identity
before mapping, and check the current help text, result counts and school identity
display. The shared dump fixture includes user_edu_school so the email tests
exercise successful same-school matching. These corrections do not change
application code or mapping rules.

Browser verification: eight tests passed in the full-suite run. The remaining
email-handoff test was corrected to click the visible search-scope label and
assert the hidden radio's checked state; its targeted rerun passed. All nine
browser tests have now passed with the corrected fixtures and selectors.
