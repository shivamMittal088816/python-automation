"""Workspace names, first-use setup and owner-only rename behaviour."""
import unittest

from tests import test_workspace_switching as switching_tests


class WorkspaceNamingTests(unittest.TestCase):
    setUp = switching_tests.WorkspaceSwitchingTests.setUp
    client = switching_tests.WorkspaceSwitchingTests.client
    spaces = switching_tests.WorkspaceSwitchingTests.spaces
    invitation = switching_tests.WorkspaceSwitchingTests.invitation
    join = switching_tests.WorkspaceSwitchingTests.join

    def rename(self, client, workspace_id, name):
        return client.request('PATCH', f'/api/v1/workspaces/{workspace_id}', json={'name': name})

    def test_initial_workspace_prompts_once_and_rename_preserves_files_and_selection(self):
        before = self.spaces(self.owner)
        identifier = before['active_workspace_id']
        self.assertTrue(before['workspaces'][0]['needs_name'])
        original = self.owner.get('/api/v1/mapping/session').json()
        renamed = self.rename(self.owner, identifier, '  Greenfield Admissions  ')
        self.assertEqual(renamed.status_code, 200, renamed.text)
        self.assertEqual(renamed.json()['name'], 'Greenfield Admissions')
        after = self.spaces(self.owner)
        self.assertEqual(after['active_workspace_id'], identifier)
        self.assertFalse(after['workspaces'][0]['needs_name'])
        self.assertEqual(self.owner.get('/api/v1/mapping/session').json(), original)
        self.assertEqual(self.spaces(self.client(self.owner.user_id))['workspaces'][0]['name'], 'Greenfield Admissions')

    def test_named_creation_works_for_both_workflows_and_allows_duplicate_names(self):
        for workflow in ('mapping', 'bulk_registration'):
            for _ in range(2):
                created = self.owner.post('/api/v1/workspaces', json={'workflow': workflow, 'name': '  School 2026  '})
                self.assertEqual(created.status_code, 201, created.text)
                spaces = self.spaces(self.owner, workflow)
                selected = next(item for item in spaces['workspaces'] if item['id'] == spaces['active_workspace_id'])
                self.assertEqual(selected['name'], 'School 2026')
                self.assertFalse(selected['needs_name'])

    def test_invalid_names_do_not_create_or_change_workspace(self):
        before = self.spaces(self.owner)
        for name in ('', '   ', 'a' * 101, 'School\nAdmissions'):
            self.assertEqual(self.owner.post('/api/v1/workspaces', json={'workflow': 'mapping', 'name': name}).status_code, 422)
            self.assertEqual(self.rename(self.owner, before['active_workspace_id'], name).status_code, 422)
        self.assertEqual(self.spaces(self.owner), before)

    def test_shared_editors_viewers_and_strangers_cannot_rename_but_see_owner_changes(self):
        identifier = self.spaces(self.owner)['active_workspace_id']
        for permission in ('editor', 'viewer'):
            invitee = self.client()
            self.assertEqual(self.join(invitee, self.invitation(permission=permission)).status_code, 200)
            self.assertEqual(self.rename(invitee, identifier, 'Not allowed').status_code, 403)
            self.assertEqual(self.rename(self.owner, identifier, f'Shared {permission}').status_code, 200)
            shared = self.spaces(invitee)['workspaces'][0]
            self.assertEqual(shared['workspace_name'], f'Shared {permission}')
            self.assertEqual(shared['role'], permission)
            self.assertEqual(invitee.get('/api/v1/mapping/session').status_code, 200)
        self.assertEqual(self.rename(self.client(), identifier, 'Not allowed').status_code, 403)
