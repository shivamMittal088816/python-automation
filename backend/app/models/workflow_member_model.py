"""Application-owned collaborator records for shared workflow access."""

from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.mysql import BIGINT, BINARY, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class WorkflowMember(Base):
    __tablename__ = 'workflow_members'
    __table_args__ = (
        Index('idx_workflow_member_workspace', 'workflow_type', 'workspace_id',
              'revoked_at'),
        Index('idx_workflow_member_invitation', 'invitation_id'),
        UniqueConstraint('user_id', 'workflow_type', 'workspace_id', name='uq_member_user_workspace'),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True,
                                    autoincrement=True)
    workflow_type: Mapped[str] = mapped_column(
        Enum('mapping', 'bulk_registration', name='workflow_member_type'),
        nullable=False,
    )
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey('app_users.id'), nullable=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    member_token_hash: Mapped[bytes | None] = mapped_column(BINARY(32), nullable=True,
                                                     unique=True)
    role: Mapped[str] = mapped_column(
        Enum('owner', 'editor', 'viewer', name='workflow_member_role'),
        nullable=False,
    )
    invitation_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey('workflow_invitations.id', ondelete='SET NULL'),
        nullable=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'),
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6),
                                                               nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

