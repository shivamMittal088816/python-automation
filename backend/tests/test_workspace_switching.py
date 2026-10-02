"""Account workspace selection, persistence and isolation on isolated APIs."""
from datetime import datetime, timedelta, timezone
import unittest

from sqlalchemy import select

from app.auth.services.cookies import cookie_name as identity_cookie
from app.models.workflow_member_model import WorkflowMember
from tests import test_invitation_join as invitation_tests


class WorkspaceSwitchingTests(unittest.TestCase):
    setUp = invitation_tests.InvitationJoinTests.setUp
    client = invitation_tests.InvitationJoinTests.client
    invitation = invitation_tests.InvitationJoinTests.invitation
    join = invitation_tests.InvitationJoinTests.join

    def spaces(self, client, workflow='mapping'):
        response = client.get(f'/api/v1/workspaces?workflow={workflow}')
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def switch(self, client, identifier, workflow='mapping'):
        return client.post('/api/v1/workspaces/select', json={'workflow': workflow, 'workspace_id': identifier})

    def test_four_memberships_and_personal_workspace_remain_selectable(self):
        recipient = self.client()
        recipient.post('/api/v1/mapping/session', json={'school_index': '100'})
        identity = recipient.cookies[identity_cookie()]
        own = self.spaces(recipient)['active_workspace_id']
        shared_ids = []
        for index in range(4):
            owner = self.client()
            owner.post('/api/v1/mapping/session', json={'school_index': str(200 + index)})
            token = owner.post('/api/v1/invitations', json={
                'workflow': 'mapping', 'permission': 'viewer' if index == 0 else 'editor'
            }).json()['invitation_url'].rsplit('/', 1)[1]
            self.assertEqual(self.join(recipient, token).status_code, 200)
            shared_ids.append(self.spaces(recipient)['active_workspace_id'])
        self.assertEqual(recipient.cookies[identity_cookie()], identity)
        self.assertEqual(len(self.spaces(recipient)['workspaces']), 5)
        self.assertEqual(self.switch(recipient, own).status_code, 200)
        personal = recipient.get('/api/v1/mapping/session').json()
        self.assertEqual(personal['settings']['workspace_school_index'], '100')
        self.assertEqual(personal['role'], 'owner')
        for index, identifier in enumerate(shared_ids):
            self.assertEqual(self.switch(recipient, identifier).status_code, 200)
            restored = recipient.get('/api/v1/mapping/session').json()
            self.assertEqual(restored['settings']['workspace_school_index'], str(200 + index))
            self.assertEqual(restored['role'], 'viewer' if index == 0 else 'editor')
        self.switch(recipient, shared_ids[0])
        denied = recipient.post('/api/v1/mapping/files/school/clear', json={}, headers={'X-Workspace-Revision': '0'})
        self.assertEqual(denied.status_code, 403)

    def test_create_personal_workspace_from_shared_preserves_membership_and_old_own_space(self):
        recipient = self.client()
        recipient.post('/api/v1/mapping/session', json={})
        own = self.spaces(recipient)['active_workspace_id']
        self.join(recipient, self.invitation())
        shared = self.spaces(recipient)['active_workspace_id']
        created = recipient.post('/api/v1/workspaces', json={'workflow': 'mapping'})
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(recipient.get('/api/v1/mapping/session').json()['role'], 'owner')
        self.assertEqual(len(self.spaces(recipient)['workspaces']), 3)
        for identifier in (own, shared):
            self.assertEqual(self.switch(recipient, identifier).status_code, 200)
        self.assertEqual(recipient.get('/api/v1/mapping/session').json()['workspace_id'], self.shared['workspace_id'])

    def test_cannot_select_another_browser_workspace_or_use_stale_tab_selection(self):
        recipient = self.client()
        recipient.post('/api/v1/mapping/session', json={})
        own = self.spaces(recipient)['active_workspace_id']
        foreign = self.spaces(self.owner)['active_workspace_id']
        self.assertEqual(self.switch(recipient, foreign).status_code, 403)
        self.assertEqual(self.spaces(recipient)['active_workspace_id'], own)
        self.join(recipient, self.invitation())
        stale = recipient.post('/api/v1/mapping/files/school/clear', json={}, headers={
            'X-Workspace-Revision': '0', 'X-Active-Workspace': own})
        self.assertEqual(stale.status_code, 409, stale.text)
        self.assertEqual(self.owner.get('/api/v1/mapping/session').json()['revision'], 0)

    def test_revocation_and_role_changes_are_checked_on_every_request(self):
        recipient = self.client()
        recipient.post('/api/v1/mapping/session', json={})
        own = self.spaces(recipient)['active_workspace_id']
        self.join(recipient, self.invitation())
        shared = self.spaces(recipient)['active_workspace_id']
        with self.factory() as db:
            member = db.scalar(select(WorkflowMember))
            member.role = 'viewer'
            db.commit()
        self.assertEqual(recipient.get('/api/v1/mapping/session').json()['role'], 'viewer')
        with self.factory() as db:
            member = db.scalar(select(WorkflowMember))
            member.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
        self.assertEqual(recipient.get('/api/v1/mapping/session').status_code, 403)
        self.assertEqual(self.switch(recipient, shared).status_code, 403)
        self.assertEqual(self.switch(recipient, own).status_code, 200)
        self.assertEqual(recipient.get('/api/v1/mapping/session').json()['role'], 'owner')

    def test_duplicate_and_self_invites_are_rejected_even_when_not_selected(self):
        recipient = self.client()
        recipient.post('/api/v1/mapping/session', json={})
        own = self.spaces(recipient)['active_workspace_id']
        own_token = recipient.post('/api/v1/invitations', json={'workflow': 'mapping'}).json()['invitation_url'].rsplit('/', 1)[1]
        self.join(recipient, self.invitation())
        self.assertEqual(self.join(recipient, own_token).status_code, 409)
        self.switch(recipient, own)
        self.assertEqual(self.join(recipient, self.invitation()).status_code, 409)

    def test_bulk_switching_and_both_invitation_keep_workflow_selections_separate(self):
        recipient = self.client()
        recipient.post('/api/v1/mapping/session', json={})
        recipient.post('/api/v1/bulk-reg/workspace')
        own_mapping = self.spaces(recipient)['active_workspace_id']
        own_bulk = self.spaces(recipient, 'bulk_registration')['active_workspace_id']
        self.assertEqual(self.join(recipient, self.invitation(workflow='both')).status_code, 200)
        shared_bulk = self.spaces(recipient, 'bulk_registration')['active_workspace_id']
        self.assertEqual(self.switch(recipient, own_mapping).status_code, 200)
        self.assertEqual(recipient.get('/api/v1/mapping/session').json()['role'], 'owner')
        self.assertEqual(recipient.get('/api/v1/bulk-reg/workspace').json()['role'], 'editor')
        self.assertEqual(self.switch(recipient, own_bulk, 'bulk_registration').status_code, 200)
        self.assertEqual(recipient.get('/api/v1/bulk-reg/workspace').json()['role'], 'owner')
        self.assertEqual(self.switch(recipient, shared_bulk, 'bulk_registration').status_code, 200)
        stale = recipient.delete('/api/v1/bulk-reg/file', headers={
            'X-Workspace-Revision': '0', 'X-Active-Workspace': own_bulk})
        self.assertEqual(stale.status_code, 409)

    def test_another_device_restores_owned_and_shared_workspaces_by_account(self):
        recipient = self.client()
        recipient.post('/api/v1/mapping/session', json={})
        self.join(recipient, self.invitation())
        device = self.client(recipient.user_id)
        self.assertEqual(list(device.cookies), [identity_cookie()])
        listed = self.spaces(device)
        self.assertEqual(len(listed['workspaces']), 2)
        self.assertEqual(device.get('/api/v1/mapping/session').json()['role'], 'editor')
        owned = next(item for item in listed['workspaces'] if item['owned'])
        self.assertEqual(self.switch(device, owned['id']).status_code, 200)
        self.assertEqual(device.get('/api/v1/mapping/session').json()['role'], 'owner')
        self.assertEqual(recipient.get('/api/v1/mapping/session').json()['role'], 'owner')

    def test_member_expiry_prevents_selection_and_forged_public_ids_do_not_grant_access(self):
        recipient = self.client()
        self.join(recipient, self.invitation())
        shared = self.spaces(recipient)['active_workspace_id']
        with self.factory() as db:
            member = db.scalar(select(WorkflowMember))
            member.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
            db.commit()
        self.assertEqual(recipient.get('/api/v1/mapping/session').status_code, 403)
        self.assertEqual(self.switch(recipient, shared).status_code, 403)
        self.assertEqual(self.switch(recipient, 'a' * 64).status_code, 403)

    def test_invitation_targets_selected_owned_workspace_instead_of_last_owner_cookie(self):
        own = self.spaces(self.owner)['active_workspace_id']
        self.owner.post('/api/v1/workspaces', json={'workflow': 'mapping'})
        self.assertEqual(self.switch(self.owner, own).status_code, 200)
        recipient = self.client()
        self.assertEqual(self.join(recipient, self.invitation()).status_code, 200)
        self.assertEqual(recipient.get('/api/v1/mapping/session').json()['workspace_id'], self.shared['workspace_id'])

    def test_both_invitation_without_legacy_owner_cookie_registers_owned_workspaces(self):
        owner = self.client()
        response = owner.post('/api/v1/invitations', json={'workflow': 'both'})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(len(self.spaces(owner)['workspaces']), 1)
        self.assertEqual(len(self.spaces(owner, 'bulk_registration')['workspaces']), 1)

    def test_self_invite_is_rejected_from_a_different_device_of_the_owner(self):
        token = self.invitation()
        device = self.client(self.owner.user_id)
        self.assertEqual(self.join(device, token).status_code, 409)
        recipient = self.client()
        self.assertEqual(self.join(recipient, token).status_code, 200)

    def test_membership_survives_invitation_lifetime_and_rejoin_reuses_revoked_record(self):
        recipient = self.client()
        self.assertEqual(self.join(recipient, self.invitation()).status_code, 200)
        with self.factory() as db:
            member = db.scalar(select(WorkflowMember))
            member.joined_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=4)
            member_id = member.id
            self.assertIsNone(member.expires_at)
            self.assertIsNone(member.member_token_hash)
            db.commit()
        self.assertEqual(recipient.get('/api/v1/mapping/session').status_code, 200)
        with self.factory() as db:
            db.get(WorkflowMember, member_id).revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
        self.assertEqual(self.join(recipient, self.invitation(permission='viewer')).status_code, 200)
        with self.factory() as db:
            members = db.scalars(select(WorkflowMember)).all()
            self.assertEqual(len(members), 1)
            self.assertEqual(members[0].id, member_id)
        self.assertEqual(recipient.get('/api/v1/mapping/session').json()['role'], 'viewer')

    def test_legacy_workflow_cookies_cannot_grant_another_account_access(self):
        from app.api.session_cookie import cookie_name
        from app.workspaces.models import Workspace
        recipient = self.client()
        with self.factory() as db:
            storage_id = db.scalar(select(Workspace)).storage_id
        recipient.cookies[cookie_name()] = storage_id
        recipient.cookies['workflow-member-mapping'] = 'forged-member-token'
        recipient.cookies['workspace-session'] = 'forged-browser-identity'
        self.assertEqual(self.spaces(recipient)['workspaces'], [])
        self.assertEqual(recipient.get('/api/v1/mapping/session').status_code, 409)
        self.assertEqual(self.switch(recipient, self.spaces(self.owner)['active_workspace_id']).status_code, 403)

    def test_database_selection_still_requires_current_membership(self):
        from app.workspaces.models import Workspace, WorkspacePreference
        recipient = self.client()
        recipient.post('/api/v1/mapping/session', json={})
        with self.factory() as db:
            foreign = db.scalar(select(Workspace).where(Workspace.owner_user_id == self.owner.user_id))
            db.get(WorkspacePreference, (recipient.user_id, 'mapping')).active_workspace_id = foreign.id
            db.commit()
        self.assertEqual(recipient.get('/api/v1/mapping/session').status_code, 403)

    def test_account_workspaces_survive_old_inactivity_cleanup(self):
        import time
        from app.api import file_workflow_state
        from app.services import bulk_registration_storage
        self.owner.post('/api/v1/bulk-reg/workspace')
        future = time.time() + 4 * 24 * 60 * 60
        self.assertEqual(file_workflow_state.cleanup_expired_sessions(future), 0)
        self.assertEqual(bulk_registration_storage.cleanup_expired_workspaces(future), 0)
        self.assertEqual(self.owner.get('/api/v1/mapping/session').status_code, 200)
        self.assertEqual(self.owner.get('/api/v1/bulk-reg/workspace').status_code, 200)

    def test_bulk_owner_reset_invalidates_old_shared_workspace(self):
        recipient = self.client()
        self.assertEqual(self.join(recipient, self.invitation(workflow='bulk_registration')).status_code, 200)
        shared = self.spaces(recipient, 'bulk_registration')['active_workspace_id']
        reset = self.owner.delete('/api/v1/bulk-reg/workspace', headers={'X-Workspace-Revision': '0'})
        self.assertEqual(reset.status_code, 200, reset.text)
        self.assertEqual(recipient.get('/api/v1/bulk-reg/workspace').status_code, 410)
        self.assertEqual(self.switch(recipient, shared, 'bulk_registration').status_code, 410)
        owned = self.spaces(self.owner, 'bulk_registration')
        self.assertEqual(len(owned['workspaces']), 1)
        self.assertNotEqual(owned['active_workspace_id'], shared)

    def test_member_owner_role_does_not_substitute_for_workspace_ownership(self):
        recipient = self.client()
        self.assertEqual(self.join(recipient, self.invitation()).status_code, 200)
        with self.factory() as db:
            db.scalar(select(WorkflowMember)).role = 'owner'
            db.commit()
        for result in (
            recipient.get('/api/v1/mapping/session'),
            recipient.get('/api/v1/invitations/members?workflow=mapping'),
            recipient.post('/api/v1/invitations', json={'workflow': 'mapping'}),
            recipient.post('/api/v1/mapping/files/school/clear', json={}, headers={'X-Workspace-Revision': '0'}),
        ):
            self.assertEqual(result.status_code, 403, result.text)

    def test_workflow_specific_invitation_context_rejects_stale_selection(self):
        from app.models.workflow_invitation_model import WorkflowInvitation
        original = self.spaces(self.owner)['active_workspace_id']
        self.owner.post('/api/v1/workspaces', json={'workflow': 'mapping'})
        headers = {'X-Mapping-Workspace': original}
        generated = self.owner.post('/api/v1/invitations', json={'workflow': 'mapping'}, headers=headers)
        members = self.owner.get('/api/v1/invitations/members?workflow=mapping', headers=headers)
        for result in (generated, members):
            self.assertEqual(result.status_code, 409, result.text)
            self.assertEqual(result.headers.get('x-workspace-selection-conflict'), '1')
        with self.factory() as db:
            self.assertEqual(db.scalars(select(WorkflowInvitation)).all(), [])

    def test_both_invitation_checks_each_workflow_context_before_creating(self):
        self.owner.post('/api/v1/bulk-reg/workspace')
        mapping = self.spaces(self.owner)['active_workspace_id']
        old_bulk = self.spaces(self.owner, 'bulk_registration')['active_workspace_id']
        self.owner.post('/api/v1/workspaces', json={'workflow': 'bulk_registration'})
        rejected = self.owner.post('/api/v1/invitations', json={'workflow': 'both'}, headers={
            'X-Mapping-Workspace': mapping, 'X-Bulk-Registration-Workspace': old_bulk})
        self.assertEqual(rejected.status_code, 409, rejected.text)
        current_bulk = self.spaces(self.owner, 'bulk_registration')['active_workspace_id']
        accepted = self.owner.post('/api/v1/invitations', json={'workflow': 'both'}, headers={
            'X-Mapping-Workspace': mapping, 'X-Bulk-Registration-Workspace': current_bulk})
        self.assertEqual(accepted.status_code, 201, accepted.text)
