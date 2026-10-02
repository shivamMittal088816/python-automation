"""Account-owned workspaces and per-workflow active selection."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database import Base


class Workspace(Base):
    __tablename__ = 'workspaces'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    name_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    workflow_type: Mapped[str] = mapped_column(String(32), index=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey('app_users.id'), index=True)
    storage_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    __table_args__ = (UniqueConstraint('workflow_type', 'storage_id', name='uq_workspace_storage'),)


class WorkspacePreference(Base):
    __tablename__ = 'user_workspace_preferences'
    user_id: Mapped[str] = mapped_column(ForeignKey('app_users.id', ondelete='CASCADE'), primary_key=True)
    workflow_type: Mapped[str] = mapped_column(String(32), primary_key=True)
    active_workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'))
    updated_at: Mapped[datetime] = mapped_column(DateTime)
