"""HTTP transport inputs for the existing file-mapping workflows."""
from typing import Literal
from pydantic import BaseModel


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


class MoveInput(BaseModel):
    filename: str
    selected_rows: list[int]
    destination: str
    version: str


class EmailInput(BaseModel):
    email_column: str
    name_column: str


class EmailSecondPassInput(BaseModel):
    name_column: str


class FullNameInput(BaseModel):
    source: Literal['Admission mapping — Not matched', 'Email mapping — Not matched']
    name_column: str
    class_column: str
    round: Literal[1, 2] = 1


class AdmissionSecondPassInput(BaseModel):
    name_column: str
