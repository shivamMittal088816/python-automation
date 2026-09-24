"""Compatibility imports for workflow routes; implementations live in focused modules."""
from Backend.api.file_workflow_constants import (
    FILES,
    STAGES,
    SOURCES,
)
from Backend.api.file_workflow_validation import (
    fail,
    require_dump_school_index,
)
from Backend.api.file_workflow_snapshots import (
    read_snapshot,
    sheets,
    selected_sheet,
    add_snapshot,
)
from Backend.api.file_workflow_responses import (
    records,
    result_pass,
    mapping_run_columns,
    summary,
    page_response,
)
from Backend.api.file_workflow_configuration import (
    suggest,
    admission_configuration,
)

__all__ = ['FILES', 'STAGES', 'SOURCES', 'fail', 'read_snapshot', 'sheets', 'records', 'selected_sheet', 'suggest', 'admission_configuration', 'result_pass', 'mapping_run_columns', 'summary', 'add_snapshot', 'page_response', 'require_dump_school_index']
