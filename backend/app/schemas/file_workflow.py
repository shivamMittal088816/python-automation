"""HTTP transport inputs for the file-mapping workflows."""
from pydantic import BaseModel
from typing import Literal


class CreateSession(BaseModel):
    school_index: str | None = None


class AdmissionRunInput(BaseModel):
    admission_school_sheet: str | None = None
    admission_dump_sheet: str | None = None
    school_admission_col: str | None = None
    school_name_col: str | None = None


class FilePathInput(BaseModel):
    path: str


class SchoolInput(BaseModel):
    school_index: str


class SchoolDetails(SchoolInput):
    school_name: str | None = None


class EmailInput(BaseModel):
    email_column: str
    name_column: str
    source: Literal['school_file', 'admission_not_matched'] = 'school_file'


class FullNameInput(BaseModel):
    name_column: str
    class_column: str
    source: Literal['school_file', 'admission_not_matched', 'email_not_matched'] = 'school_file'
