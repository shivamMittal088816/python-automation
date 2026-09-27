"""Request models shared by bulk-registration routes."""
from pydantic import BaseModel


class FilePathInput(BaseModel):
    path: str
    sheet: str | None = None


class StoredFileInput(BaseModel):
    sheet: str | None = None


class SchoolInput(BaseModel):
    school_index: str
