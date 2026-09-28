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

# Purpose: HTTP transport inputs for the file-mapping workflows.
# Its public interface includes CreateSession, AdmissionRunInput, FilePathInput, SchoolInput, SchoolDetails, EmailInput and 1 additional helpers.
# It documents and validates data crossing the HTTP boundary.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.file_workflow_routes.admission_mapping, app.routes.file_workflow_routes.configuration_preview, app.routes.file_workflow_routes.email_mapping.
# It also has 3 additional direct importers in the backend.
# Tests and higher-level workflows exercise this behavior through its public callers.
