"""Evaluate current member revocation and expiry."""
from app.common.time import now


def member_status(member):
    if member.revoked_at:
        return 'revoked'
    if member.expires_at and member.expires_at <= now():
        return 'expired'
    return 'active'
