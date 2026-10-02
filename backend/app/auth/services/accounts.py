"""Create accounts and verify credentials before issuing login sessions."""
import logging
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth.models import User
from app.auth.services.passwords import DUMMY_HASH, hash_password, verify_password
from app.auth.services.sessions import issue_session
from app.common.time import now

logger = logging.getLogger('uvicorn.error')


def register_account(payload, request, response, db):
    try:
        user = User(id=str(uuid4()), name=payload.name, email=payload.email,
                    password_hash=hash_password(payload.password), is_active=True,
                    created_at=now(), updated_at=now())
        db.add(user)
        db.flush()
        return issue_session(db, request, response, user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'An account with this email already exists. Sign in instead.')
    except SQLAlchemyError:
        db.rollback()
        logger.exception('Account creation database operation failed')
        raise HTTPException(503, 'Account creation is temporarily unavailable. Please try again shortly.')


def sign_in(payload, request, response, db):
    try:
        user = db.scalar(select(User).where(User.email == payload.email))
        valid = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
        if not valid or not user or not user.is_active:
            raise HTTPException(401, 'Email or password is incorrect.')
        return issue_session(db, request, response, user)
    except SQLAlchemyError:
        db.rollback()
        logger.exception('Login database operation failed')
        raise HTTPException(503, 'Sign-in is temporarily unavailable. Please try again shortly.')
