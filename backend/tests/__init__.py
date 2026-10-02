"""Legacy workflow tests exercise anonymous storage independently of authentication.

Auth tests explicitly enable the production-default guard on isolated databases.
"""
import os
os.environ.setdefault('AUTH_REQUIRED', 'false')
from app.config.settings import settings
settings.AUTH_REQUIRED = os.environ['AUTH_REQUIRED'].lower() == 'true'
