"""Cookie-only workflow session transport."""
from typing import Annotated
from fastapi import Depends, Header, HTTPException, Request, Response
from Backend.config.settings import settings
from Backend.api.file_workflow_state import session_folder

COOKIE_MAX_AGE_SECONDS = 72 * 60 * 60


def cookie_name():
    return '__Host-student-mapping-session' if settings.SESSION_COOKIE_SECURE else 'student_mapping_session'


def verify_origin(request: Request):
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return
    origin = request.headers.get('origin')
    allowed = {value.strip().rstrip('/') for value in settings.CORS_ORIGINS.split(',')}
    allowed.add(str(request.base_url).rstrip('/'))
    if request.headers.get('sec-fetch-site') == 'cross-site' or (origin and origin.rstrip('/') not in allowed):
        raise HTTPException(403, 'Request origin is not allowed.')


def require_session(request: Request, response: Response):
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
    return value


SessionId = Annotated[str, Depends(require_session)]
WorkspaceRevision = Annotated[int, Header(alias='X-Workspace-Revision', ge=0)]


def set_session_cookie(response: Response, session_id: str):
    legacy_name = '__Host-workflow' if settings.SESSION_COOKIE_SECURE else 'workflow_session'
    response.delete_cookie(legacy_name, path='/', secure=settings.SESSION_COOKIE_SECURE,
                           httponly=True, samesite='lax')
    response.set_cookie(cookie_name(), session_id, httponly=True,
                        secure=settings.SESSION_COOKIE_SECURE, samesite='lax', path='/',
                        max_age=COOKIE_MAX_AGE_SECONDS)
    response.headers['Cache-Control'] = 'no-store'
