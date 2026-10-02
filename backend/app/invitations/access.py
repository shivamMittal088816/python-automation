"""Enforce the selected account membership's permissions on each request."""
from fastapi import HTTPException
from app.config.settings import settings


def member_cookie_name(workflow):
    prefix = '__Host-' if settings.SESSION_COOKIE_SECURE else ''
    return f'{prefix}workflow-member-{workflow}'


def member_access(request, workflow):
    from app.workspaces.services.access import selected_access
    selected = selected_access(request, workflow)
    if selected is None or selected['role'] == 'owner':
        return None
    return _authorize_member(request, workflow, selected)


def _authorize_member(request, workflow, access):
    # Viewer authorization is enforced server-side for every workspace operation.
    read_only_preview = request.method == 'POST' and request.url.path.endswith('/mapping/configuration-preview')
    if access['role'] == 'viewer' and request.method not in ('GET', 'HEAD', 'OPTIONS') and not read_only_preview:
        raise HTTPException(403, 'Viewer access is read-only. Ask the owner for an editor invitation.')
    if request.method == 'DELETE' and request.url.path.endswith(('/session', '/workspace')):
        raise HTTPException(403, 'Only the workspace owner can reset a shared workspace.')
    setattr(request.state, f'collaborator_{workflow}', access)
    return access
