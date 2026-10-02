"""Cookie lookup, revision checks, and browser-safe workspace responses."""
from hashlib import sha256
from fastapi import HTTPException, Request, Response

from app.config.settings import settings
from app.services.bulk_registration_storage import create_workspace, load_workspace


BULK_COOKIE = '__Host-bulk-registration' if settings.SESSION_COOKIE_SECURE else 'bulk_registration_workspace'


def set_workspace_cookie(response, workspace_id):
    response.set_cookie(BULK_COOKIE, workspace_id, httponly=True,
                        secure=settings.SESSION_COOKIE_SECURE,
                        samesite=settings.SESSION_COOKIE_SAMESITE, path='/')


def workspace_for(request: Request, response: Response, *, allow_create=False):
    from app.workspaces.services.access import selected_access
    from app.workspaces.services.ownership import register_owned
    from app.workspaces.services.identity import public_id
    selected = selected_access(request, 'bulk_registration')
    from app.invitations.access import member_access
    access = member_access(request, 'bulk_registration', selected=selected) if selected else None
    if access:
        state = load_workspace(access['workspace_id'])
        state['_access_role'] = access['role']
        response.headers['X-Active-Workspace'] = public_id('bulk_registration', access['workspace_id'])
        return access['workspace_id'], state
    authenticated = getattr(request.state, 'auth_user', None) is not None
    workspace_id = selected['storage_id'] if selected else (None if authenticated else request.cookies.get(BULK_COOKIE))
    try:
        state = load_workspace(workspace_id) if workspace_id else None
    except HTTPException as exc:
        if exc.status_code != 404:
            raise
        state = None
    if state is None:
        # Only explicit initialization may replace the cookie. Delayed reads
        # and mutations must never replace a workspace created by a reset.
        if not allow_create:
            raise HTTPException(409, 'Bulk registration workspace expired or was reset. Reload and try again.')
        workspace_id = create_workspace(persistent=authenticated)
        state = load_workspace(workspace_id)
        if authenticated:
            register_owned(request, response, 'bulk_registration', workspace_id, workspace_id)
        else:
            set_workspace_cookie(response, workspace_id)
    state['_access_role'] = 'owner'
    response.headers['X-Active-Workspace'] = public_id('bulk_registration', workspace_id)
    return workspace_id, state


def require_revision(state, expected_revision):
    if expected_revision != int(state.get('revision', 0)):
        raise HTTPException(409, 'Bulk registration changed in another tab or request. Reload and try again.')


def workspace_summary(state):
    return {
        'role': state.get('_access_role', 'owner'),
        # A stable identity for reset detection, without exposing the cookie token.
        'workspace_id': sha256(state['workspace_id'].encode()).hexdigest(),
        'revision': int(state.get('revision', 0)), 'path': state.get('path', ''),
        'file': state.get('file'), 'source': {'stored': True} if state.get('input') else None,
        'schoolIndex': state.get('school_index', ''), 'school': state.get('school'),
        'output': state.get('output'),
        'outputVerified': bool(state.get('output_verified')),
    }

# Purpose: Cookie lookup, revision checks, and browser-safe workspace responses.
# Its public interface includes set_workspace_cookie, workspace_for, require_revision, workspace_summary.
# It translates HTTP input into service calls and returns API responses.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.conversion_routes, app.routes.bulk_registration.file_routes, app.routes.bulk_registration.school_routes.
# It also has 1 additional direct importer in the backend.
# Tests and higher-level workflows exercise this behavior through its public callers.
