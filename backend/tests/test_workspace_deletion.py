"""Owner-only soft deletion retains data and blocks access for both workflows."""
import unittest
from unittest.mock import patch

from sqlalchemy import inspect, select

from app.api.file_workflow_state import session_folder
from app.models.workflow_invitation_model import WorkflowInvitation
from app.models.workflow_member_model import WorkflowMember
from app.services.bulk_registration_storage import _folder
from app.workspaces.models import Workspace, WorkspacePreference
from tests import test_workspace_switching as switching_tests


class WorkspaceDeletionTests(unittest.TestCase):
    setUp = switching_tests.WorkspaceSwitchingTests.setUp
    client = switching_tests.WorkspaceSwitchingTests.client
    spaces = switching_tests.WorkspaceSwitchingTests.spaces
    invitation = switching_tests.WorkspaceSwitchingTests.invitation
    join = switching_tests.WorkspaceSwitchingTests.join
    switch = switching_tests.WorkspaceSwitchingTests.switch

    def delete(self, client, identifier):
        return client.delete(f'/api/v1/workspaces/{identifier}')

    def test_deleted_at_is_indexed(self):
        indexes = inspect(self.engine).get_indexes('workspaces')
        self.assertTrue(any(item['name'] == 'ix_workspaces_deleted_at'
                            and item['column_names'] == ['deleted_at'] for item in indexes))

    def test_soft_delete_preserves_files_memberships_and_invitations_and_blocks_access(self):
        for workflow, endpoint in (('mapping', '/api/v1/mapping/session'),
                                   ('bulk_registration', '/api/v1/bulk-reg/workspace')):
            with self.subTest(workflow=workflow):
                if workflow == 'bulk_registration':
                    self.owner.post(endpoint)
                identifier = self.spaces(self.owner, workflow)['active_workspace_id']
                recipient = self.client()
                self.assertEqual(self.join(recipient, self.invitation(workflow=workflow)).status_code, 200)
                unused_token = self.invitation(workflow=workflow)
                with self.factory() as db:
                    record = db.scalar(select(Workspace).where(Workspace.public_id == identifier))
                    record_id = record.id
                    folder = session_folder(record.storage_id) if workflow == 'mapping' else _folder(record.storage_id)
                    files = {path.name: path.read_bytes() for path in folder.iterdir() if path.is_file()}
                    member_ids = db.scalars(select(WorkflowMember.id)).all()
                    invite_ids = db.scalars(select(WorkflowInvitation.id)).all()
                response = self.delete(self.owner, identifier)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertIsNone(response.json()['active_workspace_id'])
                self.assertEqual(self.spaces(self.owner, workflow)['workspaces'], [])
                self.assertEqual(self.spaces(recipient, workflow)['workspaces'], [])
                self.assertIsNone(self.spaces(recipient, workflow)['active_workspace_id'])
                unavailable = recipient.get(endpoint)
                self.assertEqual(unavailable.status_code, 410)
                self.assertEqual(unavailable.json()['detail']['code'], 'workspace_removed')
                self.assertEqual(self.switch(recipient, identifier, workflow).status_code, 410)
                self.assertEqual(self.join(self.client(), unused_token).status_code, 410)
                with self.factory() as db:
                    self.assertIsNotNone(db.get(Workspace, record_id).deleted_at)
                    self.assertIsNone(db.get(WorkspacePreference, (self.owner.user_id, workflow)))
                    self.assertEqual(db.scalars(select(WorkflowMember.id)).all(), member_ids)
                    self.assertEqual(db.scalars(select(WorkflowInvitation.id)).all(), invite_ids)
                self.assertEqual({path.name: path.read_bytes() for path in folder.iterdir() if path.is_file()}, files)
                repeated = self.delete(self.owner, identifier)
                self.assertEqual(repeated.status_code, 200, repeated.text)
                self.assertEqual(repeated.json()['deleted_at'], response.json()['deleted_at'])

    def test_only_owner_can_delete_and_origin_and_identity_are_required(self):
        identifier = self.spaces(self.owner)['active_workspace_id']
        for role in ('editor', 'viewer'):
            recipient = self.client()
            self.assertEqual(self.join(recipient, self.invitation(permission=role)).status_code, 200)
            self.assertEqual(self.delete(recipient, identifier).status_code, 403)
        self.assertEqual(self.delete(self.client(), identifier).status_code, 403)
        anonymous = self.client()
        anonymous.cookies.clear()
        self.assertEqual(self.delete(anonymous, identifier).status_code, 401)
        rejected = self.owner.delete(f'/api/v1/workspaces/{identifier}', headers={'origin': 'https://untrusted.example'})
        self.assertEqual(rejected.status_code, 403)
        self.assertEqual(self.delete(self.owner, 'a' * 64).status_code, 404)
        self.assertEqual(self.delete(self.owner, 'invalid').status_code, 422)
        with self.factory() as db:
            record = db.scalar(select(Workspace).where(Workspace.public_id == identifier))
            self.assertIsNone(record.deleted_at)
        self.assertEqual(self.owner.get('/api/v1/mapping/session').status_code, 200)

    def test_deleting_active_selects_another_workspace_and_inactive_deletion_preserves_selection(self):
        original = self.spaces(self.owner)['active_workspace_id']
        created = self.owner.post('/api/v1/workspaces', json={'workflow': 'mapping', 'name': 'Another'})
        new_id = created.json()['active_workspace_id']
        deleted = self.delete(self.owner, new_id)
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertEqual(deleted.json()['active_workspace_id'], original)
        self.assertEqual(self.owner.get('/api/v1/mapping/session').status_code, 200)
        self.assertEqual(self.spaces(self.owner)['active_workspace_id'], original)
        other = self.owner.post('/api/v1/workspaces', json={'workflow': 'mapping', 'name': 'Third'}).json()['active_workspace_id']
        self.assertEqual(self.delete(self.owner, original).json()['active_workspace_id'], other)
        self.assertEqual(self.spaces(self.owner)['active_workspace_id'], other)

    def test_commit_failure_rolls_back_timestamp_and_selection(self):
        from app.workspaces.services.deletion import soft_delete_workspace
        identifier = self.spaces(self.owner)['active_workspace_id']
        with self.factory() as db:
            with patch.object(db, 'commit', side_effect=RuntimeError('database failure')):
                with self.assertRaises(RuntimeError):
                    soft_delete_workspace(db, self.owner.user_id, identifier)
        with self.factory() as db:
            record = db.scalar(select(Workspace).where(Workspace.public_id == identifier))
            self.assertIsNone(record.deleted_at)
            self.assertEqual(db.get(WorkspacePreference, (self.owner.user_id, 'mapping')).active_workspace_id, record.id)
