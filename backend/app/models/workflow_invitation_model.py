"""Application-owned invitation records for shared workflow access."""

from datetime import datetime

from sqlalchemy import CheckConstraint, Enum, Index, String, text
from sqlalchemy.dialects.mysql import BIGINT, BINARY, DATETIME, INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class WorkflowInvitation(Base):
    __tablename__ = 'workflow_invitations'
    __table_args__ = (
        CheckConstraint('max_uses IS NULL OR max_uses > 0',
                        name='chk_workflow_invitation_max_uses'),
        CheckConstraint('max_uses IS NULL OR use_count <= max_uses',
                        name='chk_workflow_invitation_use_count'),
        Index('idx_workflow_invitation_workspace', 'workflow_type', 'workspace_id'),
        Index('idx_workflow_invitation_expiry', 'expires_at'),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True,
                                    autoincrement=True)
    token_hash: Mapped[bytes] = mapped_column(BINARY(32), nullable=False, unique=True)
    workflow_type: Mapped[str] = mapped_column(
        Enum('mapping', 'bulk_registration', name='workflow_invitation_type'),
        nullable=False,
    )
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    permission: Mapped[str] = mapped_column(
        Enum('viewer', 'editor', name='workflow_invitation_permission'),
        nullable=False,
        server_default='editor',
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text('CURRENT_TIMESTAMP(6)'),
    )
    expires_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    max_uses: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True), nullable=True, server_default='1',
    )
    use_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), nullable=False, server_default='0',
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

