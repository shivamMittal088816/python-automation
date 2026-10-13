# Construct the FastAPI application and mount mapping endpoints under the configured API prefix.

from contextlib import asynccontextmanager
import logging
import re
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from app.config.settings import settings
from app.config.database import engine
from app.queries import load_query

from app.routes.student_mapping import router as student_mapping_router
from app.routes.student_mapping import health
from app.routes.file_workflows import router as file_workflows_router
from app.routes.bulk_registration import router as bulk_registration_router
from app.api.session_cookie import cookie_name
from app.routes.bulk_registration.workspace_access import BULK_COOKIE
from app.services.operation_log import finish_operation, operation_for_request


logger = logging.getLogger("uvicorn.error")
HEALTH_CHECK_QUERY = load_query('health_check.sql')


def check_database_connection():
    """Confirm connectivity with a read-only query; never log connection secrets."""
    with engine.connect() as connection:
        connection.execute(HEALTH_CHECK_QUERY)


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
        logger.exception('Unhandled API error during %s %s request_id=%s', request.method, request.url.path,
                         getattr(request.state, 'request_id', 'unavailable'),
                         exc_info=(type(exc), exc, exc.__traceback__))
        return JSONResponse(status_code=500, content={'detail': 'An unexpected server error occurred. Please try again.'})

    app.add_api_route("/", health, methods=["GET"], tags=["Health"])

    app.include_router(
        student_mapping_router,
        prefix=settings.API_V1_PREFIX
    )

    app.include_router(file_workflows_router, prefix=settings.API_V1_PREFIX)
    app.include_router(bulk_registration_router, prefix=settings.API_V1_PREFIX)
    @app.middleware('http')
    async def prevent_workflow_caching(request, call_next):
        supplied_id = request.headers.get('X-Request-ID', '')
        request_id = supplied_id if re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', supplied_id) else str(uuid4())
        request.state.request_id = request_id
        started = perf_counter()
        operation = operation_for_request(
            request.method, request.url.path,
            mapping_session=request.cookies.get(cookie_name()),
            bulk_workspace=request.cookies.get(BULK_COOKIE),
            request_id=request_id,
            client_operation_id=request.headers.get('X-Client-Operation-ID'),
        )
        try:
            response = await call_next(request)
        except Exception as exc:
            # Handle inside CORS/tracing middleware so browser-visible 500s retain
            # the same diagnostic headers and completion log as expected errors.
            response = await unexpected_error(request, exc)
        duration_ms = (perf_counter() - started) * 1000
        response.headers['X-Request-ID'] = request_id
        completed_operation = finish_operation(operation, response.status_code)
        if completed_operation:
            response.headers['X-Operation-ID'] = completed_operation['operation_id']
            response.headers['X-Operation-Status'] = completed_operation['status']
            response.headers['X-Operation-Workspace'] = (
                f"{completed_operation['scope']}:{completed_operation['workspace_id']}"
            )
            if completed_operation.get('client_operation_id'):
                response.headers['X-Client-Operation-ID'] = completed_operation['client_operation_id']
        response.headers['Server-Timing'] = f'app;dur={duration_ms:.1f}'
        if request.url.path.startswith((settings.API_V1_PREFIX + '/mapping', settings.API_V1_PREFIX + '/bulk-reg')):
            response.headers['Cache-Control'] = 'no-store'
        log = logger.error if response.status_code >= 500 else logger.warning if response.status_code >= 400 else logger.info
        log('%s %s completed status=%s duration_ms=%.1f request_id=%s',
                    request.method, request.url.path, response.status_code, duration_ms, request_id)
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_credentials=True,
        allow_headers=["Content-Type", "X-Workspace-Revision", "X-Request-ID", "X-Client-Operation-ID"],
        expose_headers=["Content-Disposition", "X-Request-ID", "X-Workspace-Revision", "X-Operation-ID", "X-Operation-Status", "X-Operation-Workspace", "X-Client-Operation-ID", "Server-Timing"],
    )

    return app

# ASGI entry point; the factory is also available for isolated application instances.
app = create_app()

# Purpose: Creates, configures, and starts the FastAPI application.
# Its public interface includes check_database_connection, lifespan, create_app.
# It participates in the backend application composition layer.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: developers or the application server invoke this module as an entry point.
# It is intentionally callable without requiring another backend module to import it.
# Tests and higher-level workflows exercise this behavior through its public callers.
