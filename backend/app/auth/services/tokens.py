"""Digest opaque tokens before persistence."""
import hashlib


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()
