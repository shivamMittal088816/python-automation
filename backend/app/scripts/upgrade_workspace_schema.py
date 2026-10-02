"""Add account workspace tables and membership identity columns; no legacy file import."""
from sqlalchemy import inspect, text
from app.config.database import engine
from app.auth.models import User, AuthSession
from app.workspaces.models import Workspace, WorkspacePreference
from app.models.workflow_invitation_model import WorkflowInvitation
from app.models.workflow_member_model import WorkflowMember


def upgrade():
    for model in (User, AuthSession, Workspace, WorkspacePreference,
                  WorkflowInvitation, WorkflowMember):
        model.__table__.create(engine, checkfirst=True)
    workspace_columns = {item['name'] for item in inspect(engine).get_columns('workspaces')}
    with engine.begin() as connection:
        if 'name_confirmed' not in workspace_columns:
            connection.execute(text('ALTER TABLE workspaces ADD COLUMN name_confirmed BOOLEAN NOT NULL DEFAULT 0'))
            connection.execute(text("UPDATE workspaces SET name_confirmed = 1 WHERE name <> 'My workspace' AND name NOT REGEXP '^My workspace [0-9]+$'"))
    columns = {item['name']: item for item in inspect(engine).get_columns('workflow_members')}
    with engine.begin() as connection:
        if 'user_id' not in columns:
            connection.execute(text('ALTER TABLE workflow_members ADD COLUMN user_id VARCHAR(36) NULL'))
        if 'expires_at' not in columns:
            connection.execute(text('ALTER TABLE workflow_members ADD COLUMN expires_at DATETIME(6) NULL'))
        if not columns['member_token_hash']['nullable']:
            connection.execute(text('ALTER TABLE workflow_members MODIFY COLUMN member_token_hash BINARY(32) NULL'))
    inspector = inspect(engine)
    unique = {item['name'] for item in inspector.get_unique_constraints('workflow_members')}
    indexes = {item['name'] for item in inspector.get_indexes('workflow_members')}
    foreign_keys = inspector.get_foreign_keys('workflow_members')
    with engine.begin() as connection:
        if 'uq_member_user_workspace' not in unique:
            connection.execute(text('ALTER TABLE workflow_members ADD CONSTRAINT uq_member_user_workspace UNIQUE (user_id, workflow_type, workspace_id)'))
        if 'ix_workflow_members_user_id' not in indexes:
            connection.execute(text('CREATE INDEX ix_workflow_members_user_id ON workflow_members (user_id)'))
        if not any(item['constrained_columns'] == ['user_id'] for item in foreign_keys):
            connection.execute(text('ALTER TABLE workflow_members ADD CONSTRAINT fk_workflow_member_user FOREIGN KEY (user_id) REFERENCES app_users(id)'))
    print('Account workspace schema is ready. No legacy workspaces were imported.')


if __name__ == '__main__':
    upgrade()
