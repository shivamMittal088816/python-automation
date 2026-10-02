"""Assemble the auth API without business logic."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import auth_origin
from app.auth.routes import accounts, sessions

router = APIRouter(prefix='/auth', tags=['Authentication'], dependencies=[Depends(auth_origin)])
router.include_router(accounts.router)
router.include_router(sessions.router)
