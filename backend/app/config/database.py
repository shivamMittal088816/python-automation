# Configure the MySQL engine, ORM base class and session factory.
# An engine manages connections; each request receives its own SessionLocal session.

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings


# All ORM models inherit this base so their table definitions share one metadata registry.
class Base(DeclarativeBase):
    pass


DATABASE_URL = URL.create(
    "mysql+pymysql",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD.get_secret_value(),
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)

# Check pooled connections before reuse; this helps detect connections closed by MySQL.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={'connect_timeout': 5, 'read_timeout': 10, 'write_timeout': 10},
)

# Repositories explicitly commit writes; the request dependency is responsible for closing sessions.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# Purpose: Configures the SQLAlchemy engine, declarative base, and database sessions.
# Its public interface includes Base.
# It keeps environment and infrastructure setup separate from request handling.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.config.dependencies, app.main, app.models.student_model.
# It also has 7 additional direct importers in the backend.
# Tests and higher-level workflows exercise this behavior through its public callers.
