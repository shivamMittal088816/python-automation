"""Workspace creation and selection request contracts."""
from typing import Literal
from pydantic import BaseModel, Field

Workflow = Literal['mapping', 'bulk_registration']


class CreateWorkspaceRequest(BaseModel):
    workflow: Workflow


class SelectWorkspaceRequest(CreateWorkspaceRequest):
    workspace_id: str = Field(pattern=r'^[a-f0-9]{64}$')
