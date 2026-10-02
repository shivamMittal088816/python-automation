"""Assemble the invitations API without business logic."""
from fastapi import APIRouter, Depends
from app.api.session_cookie import verify_origin
from app.invitations.routes import generation, join, members

router = APIRouter(tags=['Invitations'], dependencies=[Depends(verify_origin)])
router.include_router(generation.router, prefix='/invitations')
router.include_router(join.router, prefix='/invitations')
router.include_router(members.router, prefix='/invitations')
