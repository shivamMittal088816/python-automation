"""Browser-test server: actual services/API with fixture repositories, isolated disk storage."""
import atexit
import os
from pathlib import Path
import sys
import tempfile

BACKEND_ROOT=Path(__file__).resolve().parents[1]
REPOSITORY_ROOT=BACKEND_ROOT.parent
os.chdir(BACKEND_ROOT)
os.environ.setdefault('AUTH_REQUIRED', 'true')
sys.path.insert(0,str(BACKEND_ROOT))
import pandas as pd
import uvicorn
from app.api import file_workflow_state
from app.services import bulk_registration_storage
from app.routes.file_workflow_routes import email_mapping, file_inputs
from app.routes.bulk_registration import conversion_routes, school_routes
from app.services.bulk_registration import SchoolNotFoundError
from app.main import create_app
from app import main as backend_main

# This server uses fixture repositories, including a simulated startup DB check.
# The real connectivity check and its failure logging have separate unit coverage.
backend_main.check_database_connection = lambda: None

temporary=tempfile.TemporaryDirectory(prefix='student-mapping-browser-')
atexit.register(temporary.cleanup)
file_workflow_state.ROOT=Path(temporary.name)/'sessions'
bulk_registration_storage.ROOT=Path(temporary.name)/'bulk-registration'
dump=pd.read_csv(REPOSITORY_ROOT/'frontend/e2e/fixtures/dump.csv',dtype=str,keep_default_na=False)

def fetch_school_dump(index):
    if index.strip()!='914':
        raise ValueError(f'No school found for index {index}.')
    frame=dump.copy()
    frame.attrs.update(school_index='914',school_name='Test School')
    return frame

def fetch_email_dump(values):
    return dump.loc[dump.user_email.isin(list(values)) & dump.user_name.eq('bob')].copy()

file_inputs.fetch_school_dump=fetch_school_dump
email_mapping.fetch_email_dump=fetch_email_dump

def fetch_bulk_school(index):
    if index.strip() != '914':
        raise SchoolNotFoundError(f'No school found for index {index}.')
    return {'school_index': '914', 'school_name': 'Test School'}

school_routes.fetch_school = fetch_bulk_school
conversion_routes.fetch_sections = lambda: [(1, 'A'), (2, 'B')]
conversion_routes.fetch_existing_emails = lambda emails: {'existing@testschool.com'} & set(emails)
conversion_routes.fetch_existing_usernames = lambda usernames: {'ada001'} & set(usernames)
conversion_routes.fetch_available_usernames = lambda names: [
    f'{str(name).strip().lower()}{index:03d}' for index, name in enumerate(names, start=1)
]
app=create_app()
from tests.invitation_fixture import invitation_database, override_database
from tests.invitation_fixture import authenticated_client
invitation_engine, invitation_sessions = invitation_database(Path(temporary.name))
override_database(app, invitation_sessions)
from app.auth.models import User, AuthSession
for model in (User, AuthSession):
    model.__table__.create(invitation_engine, checkfirst=True)

# This endpoint exists only on this isolated test server, never on the production app.
from fastapi import Request, Response
from pydantic import BaseModel
class FixtureAccount(BaseModel):
    user_id: str | None = None
    name: str = 'Test member'

@app.post('/_test/sign-in')
def fixture_sign_in(payload: FixtureAccount, request: Request, response: Response):
    seeded = authenticated_client(app, invitation_sessions, payload.user_id, payload.name)
    from app.auth.services.cookies import cookie_name
    response.set_cookie(cookie_name(), seeded.cookies[cookie_name()], httponly=True,
                        secure=False, samesite='lax', path='/')
    return {'user_id': seeded.user_id}
atexit.register(invitation_engine.dispose)

# Review QA can change a membership in the isolated database to exercise live
# permission/revocation behavior. This route is never installed on the real app.
from typing import Literal
from sqlalchemy import select
from app.common.time import now
from app.models.workflow_member_model import WorkflowMember
from fastapi import HTTPException

class FixtureMembership(BaseModel):
    user_id: str
    workflow: Literal['mapping', 'bulk_registration']
    role: Literal['editor', 'viewer'] | None = None
    revoked: bool | None = None

@app.post('/_test/membership')
def fixture_membership(payload: FixtureMembership):
    with invitation_sessions() as db:
        member = db.scalar(select(WorkflowMember).where(
            WorkflowMember.user_id == payload.user_id,
            WorkflowMember.workflow_type == payload.workflow))
        if member is None:
            raise HTTPException(404, 'Fixture membership not found.')
        if payload.role is not None:
            member.role = payload.role
        if payload.revoked is not None:
            member.revoked_at = now() if payload.revoked else None
        db.commit()
        return {'updated': True}

if __name__=='__main__':
    uvicorn.run(app,host='127.0.0.1',port=8123)
