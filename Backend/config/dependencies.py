# FastAPI dependency that opens a database session for a request and closes it afterward.

from Backend.config.database import SessionLocal


# Yield a request-scoped database session and close it even if the request raises an error.
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()