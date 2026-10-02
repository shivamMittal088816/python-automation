"""Resolve, rotate and issue database-backed login sessions."""
from datetime import timedelta
import secrets
from app.auth.models import AuthSession, User
from app.auth.services.cookies import cookie_name, clear_workflow_cookies
from app.auth.services.tokens import token_hash
from app.common.time import now
from app.config.settings import settings


def session_user(request, db):
    token = request.cookies.get(cookie_name())
    if not token or len(token) != 43:
        return None
    session = db.get(AuthSession, token_hash(token))
    if not session or session.revoked_at or session.expires_at <= now():
        return None
    user = db.get(User, session.user_id)
    return user if user and user.is_active else None


def user_data(user):
    return {'id': user.id, 'name': user.name, 'email': user.email}


def issue_session(db, request, response, user):
    old_token = request.cookies.get(cookie_name())
    old_session = db.get(AuthSession, token_hash(old_token)) if old_token else None
    if old_session:
        old_session.revoked_at = now()
        if old_session.user_id != user.id:
            clear_workflow_cookies(response)
    elif old_token:
        clear_workflow_cookies(response)
    token = secrets.token_urlsafe(32)
    lifetime = timedelta(hours=settings.AUTH_SESSION_HOURS)
    db.add(AuthSession(token_hash=token_hash(token), user_id=user.id,
                       created_at=now(), expires_at=now() + lifetime))
    db.commit()
    response.set_cookie(cookie_name(), token, httponly=True, secure=settings.SESSION_COOKIE_SECURE,
                        samesite=settings.SESSION_COOKIE_SAMESITE, path='/', max_age=int(lifetime.total_seconds()))
    response.headers['Cache-Control'] = 'no-store'
    return {'user': user_data(user), 'required': settings.AUTH_REQUIRED}
