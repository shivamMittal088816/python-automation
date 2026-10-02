"""Use a disposable SQLite database for real invitation API/browser tests."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import asyncio
from http.cookies import SimpleCookie
import json as json_module
from types import SimpleNamespace

from app.config.dependencies import get_db


def invitation_database(folder):
    engine = create_engine(f'sqlite:///{folder / "invitations.sqlite"}',
                           connect_args={'check_same_thread': False, 'timeout': 10})

    @event.listens_for(engine, 'connect')
    def enable_foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')

    from app.auth.models import User, AuthSession, AuthRateLimit
    from app.workspaces.models import Workspace, WorkspacePreference
    for model in (User, AuthSession, AuthRateLimit, Workspace, WorkspacePreference):
        model.__table__.create(engine, checkfirst=True)

    # The production models use MySQL-specific DDL; mirror their contract here.
    with engine.begin() as connection:
        connection.exec_driver_sql('''CREATE TABLE workflow_invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, token_hash BLOB NOT NULL UNIQUE,
            workflow_type TEXT NOT NULL, workspace_id TEXT NOT NULL,
            bulk_workspace_id TEXT, permission TEXT NOT NULL DEFAULT 'editor',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL, max_uses INTEGER DEFAULT 1,
            use_count INTEGER NOT NULL DEFAULT 0, revoked_at DATETIME)''')
        connection.exec_driver_sql('''CREATE TABLE workflow_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_type TEXT NOT NULL,
            workspace_id TEXT NOT NULL, member_token_hash BLOB UNIQUE,
            user_id TEXT REFERENCES app_users(id), expires_at DATETIME,
            role TEXT NOT NULL, invitation_id INTEGER REFERENCES workflow_invitations(id),
            display_name TEXT, joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_accessed_at DATETIME, revoked_at DATETIME,
            UNIQUE(user_id, workflow_type, workspace_id))''')
    return engine, sessionmaker(bind=engine, autoflush=False)


def authenticated_client(app, factory, account_id=None, name='Test member'):
    """Issue fixture sessions directly; authentication itself has separate real-password tests."""
    import secrets
    from uuid import uuid4
    from app.auth.models import User, AuthSession
    from app.common.time import now
    from app.auth.services.tokens import token_hash
    from app.auth.services.cookies import cookie_name
    from app.auth.services.passwords import DUMMY_HASH
    from datetime import timedelta
    client = InvitationTestClient(app)
    with factory() as db:
        user = db.get(User, account_id) if account_id else None
        if user is None:
            identifier = str(uuid4())
            user = User(id=identifier, name=name, email=f'{identifier}@example.test',
                        password_hash=DUMMY_HASH, is_active=True, created_at=now(), updated_at=now())
            db.add(user)
            db.flush()
        token = secrets.token_urlsafe(32)
        db.add(AuthSession(token_hash=token_hash(token), user_id=user.id,
                           created_at=now(), expires_at=now() + timedelta(days=7)))
        client.user_id = user.id
        db.commit()
    client.cookies[cookie_name()] = token
    return client


def override_database(app, factory):
    def sessions():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = sessions


class InvitationTestClient:
    """Small ASGI transport matching the repository's dependency-free API tests."""
    def __init__(self, app):
        self.app = app
        self.headers = {}
        self.cookies = {}

    def close(self):
        pass

    def request(self, method, path, json=None, headers=None):
        async def perform():
            messages = []
            request_headers = {**self.headers, **(headers or {})}
            request_headers['content-type'] = 'application/json'
            request_headers['cookie'] = '; '.join(f'{key}={value}' for key, value in self.cookies.items())
            route, _, query = path.partition('?')
            scope = {'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
                     'method': method, 'scheme': 'http', 'path': route, 'raw_path': route.encode(),
                     'query_string': query.encode(), 'root_path': '', 'server': ('testserver', 80),
                     'client': ('testclient', 1234),
                     'headers': [(key.lower().encode(), value.encode()) for key, value in request_headers.items()]}
            async def receive():
                return {'type': 'http.request', 'body': json_module.dumps(json).encode() if json is not None else b'', 'more_body': False}
            async def send(message):
                messages.append(message)
            await self.app(scope, receive, send)
            start = next(message for message in messages if message['type'] == 'http.response.start')
            for key, value in start['headers']:
                if key == b'set-cookie':
                    cookie = SimpleCookie(value.decode())
                    for name, item in cookie.items():
                        if item['max-age'] == '0':
                            self.cookies.pop(name, None)
                        else:
                            self.cookies[name] = item.value
            body = b''.join(message.get('body', b'') for message in messages if message['type'] == 'http.response.body')
            return SimpleNamespace(status_code=start['status'], text=body.decode(), json=lambda: json_module.loads(body),
                                   headers={key.decode(): value.decode() for key, value in start['headers']},
                                   raw_headers=start['headers'])
        return asyncio.run(perform())

    def get(self, path, **kwargs):
        return self.request('GET', path, **kwargs)

    def post(self, path, **kwargs):
        return self.request('POST', path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request('DELETE', path, **kwargs)
