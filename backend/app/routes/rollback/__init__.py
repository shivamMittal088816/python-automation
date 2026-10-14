"""Assemble the focused rollback workflow routers."""

from fastapi import APIRouter

from app.routes.rollback import (
    dump_routes,
    execution_routes,
    input_routes,
    school_routes,
    workspace_routes,
)


router = APIRouter(prefix='/rollback')
for child in (
    workspace_routes.router,
    school_routes.router,
    dump_routes.router,
    execution_routes.router,
    input_routes.router,
):
    router.include_router(child)


__all__ = ['router']
