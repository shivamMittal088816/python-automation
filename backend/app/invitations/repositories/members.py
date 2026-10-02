"""Read accepted memberships with their account names and email addresses."""
from sqlalchemy import select
from app.auth.models import User
from app.models.workflow_member_model import WorkflowMember


def accepted_member_records(db, workspace_id, workflow):
    return db.execute(select(WorkflowMember, User).join(User, WorkflowMember.user_id == User.id).where(
        WorkflowMember.workspace_id == workspace_id,
        WorkflowMember.workflow_type == workflow,
        WorkflowMember.invitation_id.is_not(None),
    ).order_by(WorkflowMember.joined_at.desc(), WorkflowMember.id.desc())).all()
