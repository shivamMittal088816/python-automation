"""Rollback workspace cookie lookup and creation helpers."""

from fastapi import HTTPException

from app.config.settings import settings
from app.services import rollback as rollback_storage


ROLLBACK_COOKIE = (
    '__Host-rollback-workspace'
    if settings.SESSION_COOKIE_SECURE
    else 'rollback_workspace'
)


def set_workspace_cookie(response, workspace_id):
    response.set_cookie(
        ROLLBACK_COOKIE,
        workspace_id,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        path='/',
    )


def workspace_for(request, response, create=False):
    workspace_id = request.cookies.get(ROLLBACK_COOKIE)
    try:
        if workspace_id:
            rollback_storage.load_state(workspace_id)
            return workspace_id
    except HTTPException as exc:
        if exc.status_code != 404:
            raise
    if not create:
        return None
    workspace_id = rollback_storage.create_workspace()
    set_workspace_cookie(response, workspace_id)
    return workspace_id
