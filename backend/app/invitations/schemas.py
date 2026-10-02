from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CreateInvitationRequest(BaseModel):
    workflow: Literal['mapping', 'bulk_registration', 'both']
    permission: Literal['viewer', 'editor'] = 'editor'


class InvitationResponse(BaseModel):
    invitation_url: str
    expires_at: datetime


class JoinInvitationRequest(BaseModel):
    token: str = Field(min_length=20, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')


class JoinInvitationResponse(BaseModel):
    destination: Literal['/admission_file_page', '/bulk-reg']
    permission: Literal['viewer', 'editor']
    workflow: Literal['mapping', 'bulk_registration', 'both']
