import hashlib
import unittest
from unittest.mock import Mock, patch

from app.invitations.schemas import CreateInvitationRequest
from app.invitations.services.creation import create_invitation


class InvitationServiceTests(unittest.TestCase):
    @patch('app.invitations.services.creation.save_invitation')
    @patch('app.invitations.services.creation._workspace_id', return_value='workspace-123')
    @patch('app.invitations.services.creation.secrets.token_urlsafe', return_value='secret-token')
    def test_creates_hashed_single_use_invitation(self, _token, _workspace, save):
        payload = CreateInvitationRequest(
            workflow='mapping', permission='viewer',
        )

        response = create_invitation(Mock(), 'session-id', 'https://app.example.com', payload)

        invitation = save.call_args.args[1]
        self.assertEqual(invitation.token_hash, hashlib.sha256(b'secret-token').digest())
        self.assertNotIn(b'secret-token', invitation.token_hash)
        self.assertEqual(invitation.workspace_id, 'workspace-123')
        self.assertEqual(invitation.max_uses, 1)
        self.assertEqual(response.invitation_url,
                         'https://app.example.com/i/secret-token')

    @patch('app.invitations.services.creation.save_invitation')
    @patch('app.invitations.services.creation._workspace_id', return_value='workspace-123')
    def test_workflow_destinations_without_mapping_types(self, _workspace, save):
        for workflow, destination in (
            ('mapping', '/i'),
            ('bulk_registration', '/i/b'),
            ('both', '/i'),
        ):
            with self.subTest(workflow=workflow):
                payload = CreateInvitationRequest(workflow=workflow)
                response = create_invitation(Mock(), 'session-id', 'https://app.example.com', payload, 'bulk-123')
                self.assertTrue(response.invitation_url.startswith(
                    f'https://app.example.com{destination}/'))
                token = response.invitation_url.rsplit('/', 1)[1]
                self.assertEqual(len(token), 22)
                self.assertEqual(save.call_args.args[1].token_hash,
                                 hashlib.sha256(token.encode('utf-8')).digest())
                self.assertNotIn('mapping_types', save.call_args.args[1].__table__.columns)


if __name__ == '__main__':
    unittest.main()
