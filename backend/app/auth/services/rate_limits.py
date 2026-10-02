"""Database-backed authentication attempt limits."""
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.auth.models import AuthRateLimit
from app.auth.services.tokens import token_hash
from app.common.time import now


def rate_limit(db, request, email, action):
    current = now()
    ip = request.client.host if request.client else 'unknown'
    keys = [(f'{action}:ip:{ip}', 30), (f'{action}:email:{email}', 10)]
    for raw, maximum in keys:
        key = token_hash(raw)
        row = db.get(AuthRateLimit, key, with_for_update=True)
        if not row:
            row = AuthRateLimit(key=key, attempts=0, window_started_at=current)
            db.add(row)
        if row.window_started_at + timedelta(minutes=15) <= current:
            row.attempts = 0
            row.window_started_at = current
        if row.attempts >= maximum:
            db.rollback()
            raise HTTPException(429, 'Too many attempts. Please try again in 15 minutes.', headers={'Retry-After': '900'})
        row.attempts += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(429, 'Please wait a moment before trying again.', headers={'Retry-After': '5'})
