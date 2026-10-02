"""Serialize accepted-member details without exposing credentials."""
from app.invitations.repositories.members import accepted_member_records
from app.workspaces.services.memberships import member_status


def list_accepted_members(db, workspace_id, workflow):
    return [{'id': member.id, 'display_name': person.name, 'email': person.email,
             'workflow': member.workflow_type, 'role': member.role,
             'joined_at': member.joined_at, 'status': member_status(member)}
            for member, person in accepted_member_records(db, workspace_id, workflow)]
