"""Account workspace resolution and development-only legacy cookie transport."""
from typing import Annotated
from fastapi import Depends, Header, HTTPException, Request, Response
from app.config.settings import settings
from app.api.file_workflow_state import session_folder

COOKIE_MAX_AGE_SECONDS = 72 * 60 * 60


def cookie_name():
    return '__Host-student-mapping-session' if settings.SESSION_COOKIE_SECURE else 'student_mapping_session'


def verify_origin(request: Request):
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return
    origin = request.headers.get('origin')
    allowed = {value.strip().rstrip('/') for value in settings.CORS_ORIGINS.split(',')}
    allowed.add(str(request.base_url).rstrip('/'))
    if ((origin and origin.rstrip('/') not in allowed)
            or (not origin and request.headers.get('sec-fetch-site') == 'cross-site')):
        raise HTTPException(403, 'Request origin is not allowed.')


def require_session(request: Request, response: Response):
    from app.workspaces.services.access import selected_access
    from app.workspaces.services.identity import public_id
    selected = selected_access(request, 'mapping')
    if selected:
        response.headers['X-Active-Workspace'] = selected['id']
        if selected['role'] != 'owner':
            from app.invitations.access import member_access
            member_access(request, 'mapping', selected=selected)
        return selected['storage_id']
    if getattr(request.state, 'auth_user', None) is not None:
        raise HTTPException(409, 'No mapping workspace is selected. Create a workspace to continue.')
    value = request.cookies.get(cookie_name())
    legacy_name = '__Host-workflow' if settings.SESSION_COOKIE_SECURE else 'workflow_session'
    migrating = not value and bool(request.cookies.get(legacy_name))
    if migrating:
        value = request.cookies[legacy_name]
    if not value:
        raise HTTPException(401, 'Workflow session cookie is missing.')
    try:
        folder = session_folder(value)
    except HTTPException:
        raise HTTPException(401, 'Workflow session cookie is invalid.')
    if migrating and (folder / 'state.json').is_file():
        set_session_cookie(response, value)
    if (folder / 'state.json').is_file():
        from app.api.file_workflow_session_storage import load_state
        response.headers['X-Active-Workspace'] = public_id('mapping', load_state(folder)['workspace_id'])
    return value


SessionId = Annotated[str, Depends(require_session)]
WorkspaceRevision = Annotated[int, Header(alias='X-Workspace-Revision', ge=0)]


def set_session_cookie(response: Response, session_id: str):
    legacy_name = '__Host-workflow' if settings.SESSION_COOKIE_SECURE else 'workflow_session'
    response.delete_cookie(legacy_name, path='/', secure=settings.SESSION_COOKIE_SECURE,
                           httponly=True, samesite=settings.SESSION_COOKIE_SAMESITE)
    response.set_cookie(cookie_name(), session_id, httponly=True,
                        secure=settings.SESSION_COOKIE_SECURE,
                        samesite=settings.SESSION_COOKIE_SAMESITE, path='/',
                        max_age=COOKIE_MAX_AGE_SECONDS)
    response.headers['Cache-Control'] = 'no-store'


# Purpose: Implements the cookie transport and request security for mapping sessions.
# It selects secure or development cookie names and validates mutating-request origins.
# require_session resolves the cookie to a valid session folder and migrates legacy cookies.
# SessionId and WorkspaceRevision provide reusable FastAPI dependency annotations.
# set_session_cookie writes an HTTP-only cookie and disables response caching.
# Used by: the file-workflow router applies verify_origin to all mapping endpoints.
# Session creation writes the cookie, while protected route functions depend on SessionId.
# Mutating admission, email, file, and class routes depend on WorkspaceRevision.
