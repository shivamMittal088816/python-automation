from app.models.workflow_invitation_model import WorkflowInvitation


def save_invitation(db, invitation: WorkflowInvitation) -> WorkflowInvitation:
    """Persist an invitation, rolling back a failed transaction."""
    try:
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation
    except Exception:
        db.rollback()
        raise
