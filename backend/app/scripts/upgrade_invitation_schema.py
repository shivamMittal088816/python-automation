"""Apply additive invitation schema changes; never modify external platform tables."""
from sqlalchemy import inspect, text

from app.config.database import engine
from app.models.workflow_invitation_model import WorkflowInvitation
from app.models.workflow_member_model import WorkflowMember


def upgrade():
    WorkflowInvitation.__table__.create(engine, checkfirst=True)
    columns = {column['name']: column for column in inspect(engine).get_columns('workflow_invitations')}
    with engine.begin() as connection:
        if 'bulk_workspace_id' not in columns:
            connection.execute(text('ALTER TABLE workflow_invitations ADD COLUMN bulk_workspace_id VARCHAR(36) NULL'))
        if 'both' not in getattr(columns['workflow_type']['type'], 'enums', []):
            connection.execute(text("ALTER TABLE workflow_invitations MODIFY COLUMN workflow_type ENUM('mapping','bulk_registration','both') NOT NULL"))
    WorkflowMember.__table__.create(engine, checkfirst=True)
    print('Invitation schema is ready.')


if __name__ == '__main__':
    upgrade()
