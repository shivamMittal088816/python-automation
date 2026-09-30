"""Schema checks for workflow invitation and collaborator tables."""

import unittest

from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import mysql

from app.models.workflow_invitation_model import WorkflowInvitation
from app.models.workflow_member_model import WorkflowMember


class WorkflowCollaborationModelTests(unittest.TestCase):
    def test_invitation_table_structure(self):
        table = WorkflowInvitation.__table__

        self.assertEqual(table.name, 'workflow_invitations')
        self.assertEqual(set(table.columns), {
            table.c.id, table.c.token_hash, table.c.workflow_type,
            table.c.workspace_id, table.c.permission, table.c.created_at,
            table.c.expires_at, table.c.max_uses, table.c.use_count,
            table.c.revoked_at,
        })
        self.assertTrue(table.c.token_hash.unique)
        self.assertEqual(table.c.token_hash.type.length, 32)
        self.assertEqual(
            {index.name for index in table.indexes},
            {'idx_workflow_invitation_workspace', 'idx_workflow_invitation_expiry'},
        )

    def test_member_table_structure_and_invitation_relationship(self):
        table = WorkflowMember.__table__

        self.assertEqual(table.name, 'workflow_members')
        self.assertTrue(table.c.member_token_hash.unique)
        foreign_key = next(iter(table.c.invitation_id.foreign_keys))
        self.assertEqual(foreign_key.target_fullname, 'workflow_invitations.id')
        self.assertEqual(foreign_key.ondelete, 'SET NULL')
        self.assertEqual(
            {index.name for index in table.indexes},
            {'idx_workflow_member_workspace', 'idx_workflow_member_invitation'},
        )

    def test_tables_compile_for_mysql(self):
        invitation_sql = str(CreateTable(WorkflowInvitation.__table__).compile(
            dialect=mysql.dialect(),
        ))
        member_sql = str(CreateTable(WorkflowMember.__table__).compile(
            dialect=mysql.dialect(),
        ))

        self.assertIn('CREATE TABLE workflow_invitations', invitation_sql)
        self.assertIn('CREATE TABLE workflow_members', member_sql)
        self.assertIn('FOREIGN KEY(invitation_id)', member_sql)


if __name__ == '__main__':
    unittest.main()
