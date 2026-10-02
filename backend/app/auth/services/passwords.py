"""Salted password hashing and constant-time verification."""
import hashlib
import hmac
import secrets
from threading import Semaphore

PASSWORD_WORKERS = Semaphore(2)


def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    with PASSWORD_WORKERS:
        digest = hashlib.scrypt(password.encode(), salt=salt, n=131072, r=8, p=1,
                                maxmem=256 * 1024 * 1024, dklen=64)
    return f'scrypt$131072$8$1${salt.hex()}${digest.hex()}'


def verify_password(password, encoded):
    try:
        algorithm, n, r, p, salt, digest = encoded.split('$')
        if (algorithm, n, r, p) != ('scrypt', '131072', '8', '1'):
            return False
        actual = hash_password(password, bytes.fromhex(salt)).split('$')[-1]
        return hmac.compare_digest(actual, digest)
    except (ValueError, TypeError):
        return False


# Match password work for nonexistent accounts to reduce timing disclosure.
DUMMY_HASH = hash_password(secrets.token_urlsafe(32))
