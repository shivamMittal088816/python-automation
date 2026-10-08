"""Browser operation-correlation request models."""

from pydantic import BaseModel, Field, UUID4


class OperationStatusInput(BaseModel):
    client_operation_ids: list[UUID4] = Field(min_length=1, max_length=20)
