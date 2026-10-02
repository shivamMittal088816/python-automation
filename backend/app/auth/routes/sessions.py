"""Current-account and sign-out endpoints."""
from app.auth.models import AuthSession
from app.auth.services.cookies import cookie_name, clear_workflow_cookies
from app.auth.services.sessions import session_user, user_data
from app.auth.services.tokens import token_hash
from app.common.time import now
from app.config.settings import settings
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.config.dependencies import get_db

router = APIRouter()


@router.get('/me')
def me(request: Request, response: Response, db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    try:
        user = session_user(request, db)
        return {'user': user_data(user) if user else None, 'required': settings.AUTH_REQUIRED}
    except SQLAlchemyError:
        raise HTTPException(503, 'Sign-in is temporarily unavailable. Please try again shortly.')


@router.post('/logout', status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        token = request.cookies.get(cookie_name())
        session = db.get(AuthSession, token_hash(token)) if token else None
        if session:
            session.revoked_at = now()
            db.commit()
        response.delete_cookie(cookie_name(), path='/', httponly=True, secure=settings.SESSION_COOKIE_SECURE,
                              samesite=settings.SESSION_COOKIE_SAMESITE)
        clear_workflow_cookies(response)
        response.headers['Cache-Control'] = 'no-store'
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, 'Could not sign out. Please try again.')
