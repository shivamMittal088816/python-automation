"""Authentication cookie naming and obsolete workflow-cookie cleanup."""
from app.config.settings import settings


def cookie_name():
    return ('__Host-' if settings.SESSION_COOKIE_SECURE else '') + 'auth-session'


def clear_workflow_cookies(response):
    from app.api.session_cookie import cookie_name as mapping_cookie
    from app.invitations.access import member_cookie_name
    from app.routes.bulk_registration.workspace_access import BULK_COOKIE
    prefix = '__Host-' if settings.SESSION_COOKIE_SECURE else ''
    for name in (mapping_cookie(), prefix + 'workflow', BULK_COOKIE, prefix + 'workspace-session',
                 member_cookie_name('mapping'), member_cookie_name('bulk_registration')):
        response.delete_cookie(name, path='/', httponly=True, secure=settings.SESSION_COOKIE_SECURE,
                              samesite=settings.SESSION_COOKIE_SAMESITE)
