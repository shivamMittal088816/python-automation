"""Assemble the workspaces API without business logic."""
from fastapi import APIRouter, Depends
from app.api.session_cookie import verify_origin
from app.workspaces.routes import creation, listing, selection

router = APIRouter(tags=['Workspaces'], dependencies=[Depends(verify_origin)])
router.include_router(creation.router, prefix='/workspaces')
router.include_router(listing.router, prefix='/workspaces')
router.include_router(selection.router, prefix='/workspaces')
