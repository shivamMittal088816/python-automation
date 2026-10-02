"""Remove obsolete authentication attempt counters, preserving accounts and sessions."""
from sqlalchemy import MetaData, Table

from app.config.database import engine


def upgrade():
    Table('auth_rate_limits', MetaData()).drop(engine, checkfirst=True)
    print('Obsolete authentication rate-limit table removed.')


if __name__ == '__main__':
    upgrade()
