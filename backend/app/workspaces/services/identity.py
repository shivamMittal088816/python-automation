"""Resolve the requesting account and public workspace identifiers."""
from hashlib import sha256
from fastapi import HTTPException


def public_id(workflow, workspace_id):
    return sha256(f'{workflow}:{workspace_id}'.encode()).hexdigest()


def user_id(request):
    user = getattr(request.state, 'auth_user', None)
    if user is None:
        raise HTTPException(401, 'Please sign in to continue.', headers={'X-Authentication-Required': '1'})
    return user.id


def database(request, db=None):
    session = db if db is not None else getattr(request.state, 'auth_db', None)
    if session is None:
        raise HTTPException(503, 'Workspace access is temporarily unavailable.')
    return session
