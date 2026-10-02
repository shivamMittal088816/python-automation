# Accepted members in workspace selector

The owner dropdown loads `GET /api/v1/invitations/members?workflow=mapping` (or `bulk_registration`) each time it opens. The server resolves the logged-in user's database workspace preference and verifies ownership. Shared members cannot read the owner management list. Responses expose account names and email addresses, workflow, current membership role, join date and active/expired/revoked status, without tokens or workspace credentials.

Pending invitations are excluded. Both-workflow invitations create separate memberships, shown in the corresponding workflow dropdown. Names and email addresses come from `app_users`, joined through `workflow_members.user_id`. Edit access is a disabled placeholder; no editing endpoint or permission change is implemented.

Validation on 2026-10-02:

- Frontend production build passed.
- 17 isolated backend invitation/model tests passed, including workspace isolation, member denial, pending invitation exclusion, both-workflow listing and current role/revocation display.
- Edge browser coverage checks accepted invitee loading after reopening, viewer permission text, disabled edit control and mobile layout, alongside invitation join regressions.
- Desktop and mobile screenshots visually inspected: `.test-temp/invitation-qa/workspace-members-desktop.png` and `workspace-members-mobile.png`.
