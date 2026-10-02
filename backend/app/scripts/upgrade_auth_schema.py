"""Create only application-owned authentication tables, without changing student data."""
from app.config.database import engine
from app.auth.models import User, AuthSession


def upgrade():
    for model in (User, AuthSession):
        model.__table__.create(engine, checkfirst=True)
    print('Authentication schema is ready.')


if __name__ == '__main__':
    upgrade()
