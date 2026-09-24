# Construct the FastAPI application and mount mapping endpoints under the configured API prefix.

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from Backend.config.settings import settings
from Backend.config.database import engine

from Backend.routes.student_mapping import router as student_mapping_router
from Backend.routes.student_mapping import health
from Backend.routes.file_workflows import router as file_workflows_router


logger = logging.getLogger("uvicorn.error")


def check_database_connection():
    """Confirm connectivity with a read-only query; never log connection secrets."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@asynccontextmanager
async def lifespan(app):
    logger.info("Checking database connection...")
    try:
        await run_in_threadpool(check_database_connection)
    except SQLAlchemyError:
        # File-only workflows remain available even when MySQL is unavailable.
        logger.warning(
            "Database connection failed. Check database settings and network access. "
            "The server will start, but database-dependent features are unavailable."
        )
    else:
        logger.info("Database connected successfully.")
    yield


# Create the API instance and register its router under the configured version prefix.
def create_app():
    app = FastAPI(
        title=settings.APP_NAME,
        lifespan=lifespan,
    )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.exception('Unhandled API error during %s %s', request.method, request.url.path,
                         exc_info=(type(exc), exc, exc.__traceback__))
        return JSONResponse(status_code=500, content={'detail': 'An unexpected server error occurred. Please try again.'})

    app.add_api_route("/", health, methods=["GET"], tags=["Health"])

    app.include_router(
        student_mapping_router,
        prefix=settings.API_V1_PREFIX
    )

    app.include_router(file_workflows_router, prefix=settings.API_V1_PREFIX)
    @app.middleware('http')
    async def prevent_workflow_caching(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith(settings.API_V1_PREFIX + '/mapping'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
        allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
        allow_credentials=True,
        allow_headers=["Content-Type"],
        expose_headers=["Content-Disposition"],
    )

    return app

# ASGI entry point; the factory is also available for isolated application instances.
app = create_app()
