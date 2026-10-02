"""Verify request authorization stays fresh while avoiding redundant SQL."""
from contextlib import contextmanager
import unittest

from sqlalchemy import event

from tests import test_workspace_switching as switching_tests


class DatabaseEfficiencyTests(unittest.TestCase):
    setUp = switching_tests.WorkspaceSwitchingTests.setUp
    client = switching_tests.WorkspaceSwitchingTests.client
    spaces = switching_tests.WorkspaceSwitchingTests.spaces
    invitation = switching_tests.WorkspaceSwitchingTests.invitation
    join = switching_tests.WorkspaceSwitchingTests.join

    @contextmanager
    def queries(self):
        statements = []

        def capture(connection, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith('SELECT'):
                statements.append(statement.lower())

        event.listen(self.engine, 'before_cursor_execute', capture)
        try:
            yield statements
        finally:
            event.remove(self.engine, 'before_cursor_execute', capture)

    def test_authentication_uses_one_query_without_reading_password_hash(self):
        with self.queries() as statements:
            response = self.owner.get('/api/v1/workspaces?workflow=mapping')
        self.assertEqual(response.status_code, 200, response.text)
        authentication = [sql for sql in statements if 'auth_sessions' in sql]
        self.assertEqual(len(authentication), 1)
        self.assertNotIn('password_hash', authentication[0])

    def test_named_workspace_creation_does_not_count_previous_workspaces(self):
        with self.queries() as statements:
            response = self.owner.post('/api/v1/workspaces', json={
                'workflow': 'mapping', 'name': 'Named School'})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertFalse(any('count(' in sql for sql in statements))

    def test_shared_mapping_permission_is_resolved_once_per_request(self):
        invitee = self.client()
        self.assertEqual(self.join(invitee, self.invitation(permission='viewer')).status_code, 200)
        for method, path in [('GET', '/api/v1/mapping/session'),
                             ('POST', '/api/v1/mapping/files/school/clear')]:
            with self.queries() as statements:
                response = invitee.request(method, path, headers={'X-Workspace-Revision': '0'})
            self.assertEqual(response.status_code, 200 if method == 'GET' else 403)
            self.assertEqual(len([sql for sql in statements if 'from workflow_members' in sql]), 1)

    def test_shared_bulk_permission_is_resolved_once_per_request(self):
        self.assertEqual(self.owner.post('/api/v1/bulk-reg/workspace').status_code, 200)
        invitee = self.client()
        self.assertEqual(self.join(invitee, self.invitation(workflow='bulk_registration', permission='viewer')).status_code, 200)
        with self.queries() as statements:
            response = invitee.get('/api/v1/bulk-reg/workspace')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len([sql for sql in statements if 'from workflow_members' in sql]), 1)
