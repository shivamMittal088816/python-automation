# FastAPI dependency that opens a database session for a request and closes it afterward.

from app.config.database import SessionLocal


# Yield a request-scoped database session and close it even if the request raises an error.
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# Purpose: Provides request-scoped FastAPI dependencies such as database sessions.
# Its public interface includes get_db.
# It keeps environment and infrastructure setup separate from request handling.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.student_mapping.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
