"""Trusted-origin and authenticated-user FastAPI dependencies."""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.api.session_cookie import verify_origin
from app.auth.services.cookies import cookie_name
from app.auth.services.sessions import session_user
from app.config.dependencies import get_db
from app.config.settings import settings


def auth_origin(request: Request):
    verify_origin(request)
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and not request.headers.get('origin'):
        raise HTTPException(403, 'A trusted request origin is required.')


def require_user(request: Request, db: Session = Depends(get_db)):
    if request.url.path == settings.API_V1_PREFIX + '/mapping/health':
        return None
    if not settings.AUTH_REQUIRED and not request.cookies.get(cookie_name()):
        return None
    try:
        user = session_user(request, db)
    except SQLAlchemyError:
        raise HTTPException(503, 'Sign-in is temporarily unavailable. Please try again shortly.')
    if not user:
        raise HTTPException(401, 'Please sign in to continue.', headers={'X-Authentication-Required': '1'})
    request.state.auth_user = user
    request.state.auth_db = db
    return user
