"""HTTP validation errors and required school identity."""
from fastapi import HTTPException


def fail(message, code=422):
    raise HTTPException(code, message)


def require_dump_school_index(state):
    index = str(state.get('saved_admission_dump', {}).get('school_index') or '').strip()
    if not index or not index.isascii() or not index.isdecimal():
        fail('Enter and save the school index for the uploaded dump before starting mapping.')
    return index


# Purpose: Provides consistent HTTP validation failures for file-workflow operations.
# fail converts a domain validation message into a FastAPI HTTPException response.
# require_dump_school_index reads and normalizes the selected dump's school identity.
# It rejects missing, non-ASCII, or non-numeric values before mapping starts.
# Successful validation returns the normalized school index for downstream logic.
# Used by: admission-mapping routes validate required school identity before processing.
# File input, preview, download, and configuration routes use fail for user-facing errors.
# Snapshot and configuration helpers also use fail when stored inputs are invalid.
