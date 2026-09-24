"""HTTP validation errors and required school identity."""
from fastapi import HTTPException


def fail(message, code=422):
    raise HTTPException(code, message)


def require_dump_school_index(state):
    index = str(state.get('saved_admission_dump', {}).get('school_index') or '').strip()
    if not index or not index.isascii() or not index.isdecimal():
        fail('Enter and save the school index for the uploaded dump before starting mapping.')
    return index
