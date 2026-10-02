"""Workspace creation and selection request contracts."""
from typing import Literal
from pydantic import BaseModel, Field, field_validator

Workflow = Literal['mapping', 'bulk_registration']


class WorkflowRequest(BaseModel):
    workflow: Workflow


def clean_name(value):
    value = value.strip()
    if not 1 <= len(value) <= 100 or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError('Enter a workspace name of 1–100 characters without control characters.')
    return value


class CreateWorkspaceRequest(WorkflowRequest):
    name: str | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value):
        return clean_name(value) if value is not None else None


class RenameWorkspaceRequest(BaseModel):
    name: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, value):
        return clean_name(value)


class SelectWorkspaceRequest(WorkflowRequest):
    workspace_id: str = Field(pattern=r'^[a-f0-9]{64}$')
