"""End-to-end invitation redemption and collaborator authorization on isolated storage."""
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sqlalchemy import select

from app.api import file_workflow_state
from app.config.settings import settings
from app.main import create_app
from app.models.workflow_invitation_model import WorkflowInvitation
from app.models.workflow_member_model import WorkflowMember
from app.services import bulk_registration_storage
from tests.invitation_fixture import invitation_database, override_database, authenticated_client


class InvitationJoinTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.engine, self.factory = invitation_database(root)
        self.addCleanup(self.engine.dispose)
        for target, attribute, value in (
            (file_workflow_state, 'ROOT', root / 'mapping'),
            (bulk_registration_storage, 'ROOT', root / 'bulk'),
            (settings, 'SESSION_COOKIE_SECURE', False),
            (settings, 'AUTH_REQUIRED', True),
            (settings, 'CORS_ORIGINS', 'http://127.0.0.1:5174'),
        ):
            patcher = patch.object(target, attribute, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.app = create_app()
        override_database(self.app, self.factory)
        self.owner = self.client()
        self.shared = self.owner.post('/api/v1/mapping/session', json={'school_index': '914'}).json()

    def client(self, account_id=None):
        client = authenticated_client(self.app, self.factory, account_id)
        client.headers['origin'] = 'http://127.0.0.1:5174'
        self.addCleanup(client.close)
        return client

    def invitation(self, workflow='mapping', permission='editor'):
        response = self.owner.post('/api/v1/invitations', json={'workflow': workflow, 'permission': permission})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['invitation_url'].rsplit('/', 1)[1]

    def join(self, recipient, token):
        return recipient.post('/api/v1/invitations/join', json={'token': token})

    def test_member_listing_is_owner_scoped_and_excludes_pending_invitations(self):
        endpoint = '/api/v1/invitations/members?workflow=mapping'
        token = self.invitation(permission='viewer')
        self.assertEqual(self.owner.get(endpoint).json(), [])
        recipient = self.client()
        self.assertEqual(self.join(recipient, token).status_code, 200)
        result = self.owner.get(endpoint)
        self.assertEqual(result.status_code, 200, result.text)
        member = result.json()[0]
        self.assertEqual(member['role'], 'viewer')
        self.assertEqual(member['workflow'], 'mapping')
        self.assertEqual(member['status'], 'active')
        self.assertNotIn('member_token_hash', member)
        self.assertNotIn('workspace_id', member)
        self.assertEqual(recipient.get(endpoint).status_code, 403)
        other = self.client()
        other.post('/api/v1/mapping/session', json={})
        self.assertEqual(other.get(endpoint).json(), [])

    def test_both_invitation_members_appear_in_each_workflow_with_current_role(self):
        recipient = self.client()
        self.assertEqual(self.join(recipient, self.invitation(workflow='both')).status_code, 200)
        with self.factory() as db:
            member = db.scalar(select(WorkflowMember).where(WorkflowMember.workflow_type == 'mapping'))
            from app.auth.models import User
            db.get(User, member.user_id).name = 'Sam'
            member.role = 'viewer'
            member.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
        mapping = self.owner.get('/api/v1/invitations/members?workflow=mapping').json()[0]
        bulk = self.owner.get('/api/v1/invitations/members?workflow=bulk_registration').json()[0]
        self.assertEqual((mapping['display_name'], mapping['role'], mapping['status']), ('Sam', 'viewer', 'revoked'))
        self.assertEqual((bulk['workflow'], bulk['role']), ('bulk_registration', 'editor'))

    def test_editor_joins_existing_workspace_without_owner_cookie(self):
        recipient = self.client()
        result = self.join(recipient, self.invitation())
        self.assertEqual(result.status_code, 200, result.text)
        restored = recipient.get('/api/v1/mapping/session').json()
        self.assertEqual(restored['workspace_id'], self.shared['workspace_id'])
        self.assertEqual(restored['settings']['workspace_school_index'], '914')
        self.assertEqual(restored['role'], 'editor')
        self.assertNotIn('student_mapping_session', recipient.cookies)
        response = recipient.post('/api/v1/mapping/admission-mapping/run', json={},
                                  headers={'X-Workspace-Revision': '0'})
        self.assertEqual(response.status_code, 422)  # Authorized, but no input files.
        self.assertEqual(recipient.post('/api/v1/invitations', json={'workflow': 'mapping'}).status_code, 403)

    def test_viewer_reads_but_cannot_write_even_with_existing_owner_cookie(self):
        recipient = self.client()
        recipient.post('/api/v1/mapping/session', json={})
        self.assertEqual(self.join(recipient, self.invitation(permission='viewer')).status_code, 200)
        restored = recipient.get('/api/v1/mapping/session').json()
        self.assertEqual(restored['workspace_id'], self.shared['workspace_id'])
        self.assertEqual(restored['role'], 'viewer')
        result = recipient.post('/api/v1/mapping/admission-mapping/run', json={},
                                headers={'X-Workspace-Revision': '0'})
        self.assertEqual(result.status_code, 403, result.text)
        self.assertEqual(self.owner.get('/api/v1/mapping/session').json()['revision'], 0)
        self.assertEqual(recipient.post('/api/v1/mapping/configuration-preview', json={}).status_code, 200)

    def test_single_use_invalid_and_malformed_codes(self):
        token = self.invitation()
        self.assertEqual(self.join(self.client(), token).status_code, 200)
        self.assertEqual(self.join(self.client(), token).status_code, 409)
        self.assertEqual(self.join(self.client(), 'A' * 22).status_code, 404)
        self.assertEqual(self.join(self.client(), 'short').status_code, 422)
        with self.factory() as db:
            self.assertEqual(db.scalar(select(WorkflowInvitation)).use_count, 1)
            self.assertEqual(len(db.scalars(select(WorkflowMember)).all()), 1)

    def test_owner_cannot_accept_own_invitation_or_consume_it(self):
        for workflow in ('mapping', 'bulk_registration', 'both'):
            with self.subTest(workflow=workflow):
                token = self.invitation(workflow)
                cookies_before = dict(self.owner.cookies)
                result = self.join(self.owner, token)
                self.assertEqual(result.status_code, 409, result.text)
                self.assertIn('own workspace', result.json()['detail'])
                self.assertEqual(self.owner.cookies, cookies_before)
                with self.factory() as db:
                    row = db.scalar(select(WorkflowInvitation).where(
                        WorkflowInvitation.token_hash == hashlib.sha256(token.encode()).digest()))
                    self.assertEqual(row.use_count, 0)
                    self.assertEqual(len(db.scalars(select(WorkflowMember).where(
                        WorkflowMember.invitation_id == row.id)).all()), 0)
                self.assertEqual(self.join(self.client(), token).status_code, 200)

    def test_existing_member_cannot_consume_another_invitation(self):
        recipient = self.client()
        self.assertEqual(self.join(recipient, self.invitation()).status_code, 200)
        token = self.invitation()
        before = dict(recipient.cookies)
        result = self.join(recipient, token)
        self.assertEqual(result.status_code, 409)
        self.assertIn('already have access', result.json()['detail'])
        self.assertEqual(recipient.cookies, before)
        self.assertEqual(self.join(self.client(), token).status_code, 200)

    def test_both_rejected_when_browser_owns_only_one_target(self):
        from app.workspaces.models import Workspace
        token = self.invitation('both')
        for workflow in ('mapping', 'bulk_registration'):
            with self.subTest(workflow=workflow):
                recipient = self.client()
                with self.factory() as db:
                    record = db.scalar(select(Workspace).where(Workspace.workflow_type == workflow))
                    record.owner_user_id = recipient.user_id
                    db.commit()
                self.assertEqual(self.join(recipient, token).status_code, 409)
                with self.factory() as db:
                    record = db.scalar(select(Workspace).where(Workspace.workflow_type == workflow))
                    record.owner_user_id = self.owner.user_id
                    db.commit()
        self.assertEqual(self.join(self.client(), token).status_code, 200)

    def test_expired_revoked_and_missing_workspaces_do_not_consume_code(self):
        for scenario in ('expired', 'revoked', 'missing'):
            with self.subTest(scenario=scenario):
                token = self.invitation()
                digest = hashlib.sha256(token.encode()).digest()
                with self.factory() as db:
                    row = db.scalar(select(WorkflowInvitation).where(WorkflowInvitation.token_hash == digest))
                    if scenario == 'expired':
                        row.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
                    elif scenario == 'revoked':
                        row.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    else:
                        row.workspace_id = 'missing-workspace'
                    db.commit()
                self.assertEqual(self.join(self.client(), token).status_code, 410)
                with self.factory() as db:
                    self.assertEqual(db.scalar(select(WorkflowInvitation).where(WorkflowInvitation.token_hash == digest)).use_count, 0)

    def test_bulk_and_both_target_correct_workspaces(self):
        bulk = self.owner.post('/api/v1/bulk-reg/workspace').json()
        for workflow in ('bulk_registration', 'both'):
            with self.subTest(workflow=workflow):
                recipient = self.client()
                self.assertEqual(self.join(recipient, self.invitation(workflow)).status_code, 200)
                self.assertEqual(recipient.get('/api/v1/bulk-reg/workspace').json()['workspace_id'], bulk['workspace_id'])
                if workflow == 'both':
                    self.assertEqual(recipient.get('/api/v1/mapping/session').json()['workspace_id'], self.shared['workspace_id'])
                self.assertEqual(recipient.delete('/api/v1/bulk-reg/workspace',
                                                 headers={'X-Workspace-Revision': '0'}).status_code, 403)

    def test_bulk_viewer_cannot_mutate(self):
        recipient = self.client()
        self.assertEqual(self.join(recipient, self.invitation('bulk_registration', 'viewer')).status_code, 200)
        self.assertEqual(recipient.get('/api/v1/bulk-reg/workspace').json()['role'], 'viewer')
        self.assertEqual(recipient.delete('/api/v1/bulk-reg/file', headers={'X-Workspace-Revision': '0'}).status_code, 403)

    def test_revoked_members_and_cross_origin_redemption_are_rejected(self):
        recipient = self.client()
        self.assertEqual(self.join(recipient, self.invitation()).status_code, 200)
        with self.factory() as db:
            db.scalar(select(WorkflowMember)).revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
        self.assertEqual(recipient.get('/api/v1/mapping/session').status_code, 403)
        token = self.invitation()
        result = recipient.post('/api/v1/invitations/join', json={'token': token},
                                headers={'origin': 'https://untrusted.example'})
        self.assertEqual(result.status_code, 403)


if __name__ == '__main__':
    unittest.main()
