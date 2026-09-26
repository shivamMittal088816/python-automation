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
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)

# Check pooled connections before reuse; this helps detect connections closed by MySQL.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Repositories explicitly commit writes; the request dependency is responsible for closing sessions.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)
