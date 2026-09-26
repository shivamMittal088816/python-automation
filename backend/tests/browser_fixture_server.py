"""Browser-test server: actual services/API with fixture repositories, isolated disk storage."""
import atexit
import os
from pathlib import Path
import sys
import tempfile

BACKEND_ROOT=Path(__file__).resolve().parents[1]
REPOSITORY_ROOT=BACKEND_ROOT.parent
os.chdir(BACKEND_ROOT)
sys.path.insert(0,str(BACKEND_ROOT))
import pandas as pd
import uvicorn
from app.api import file_workflow_state
from app.routes.file_workflow_routes import email_mapping, file_inputs
from app.routes import bulk_registration
from app.main import create_app
from app import main as backend_main

# This server uses fixture repositories, including a simulated startup DB check.
# The real connectivity check and its failure logging have separate unit coverage.
backend_main.check_database_connection = lambda: None

temporary=tempfile.TemporaryDirectory(prefix='student-mapping-browser-')
atexit.register(temporary.cleanup)
file_workflow_state.ROOT=Path(temporary.name)/'sessions'
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
        raise bulk_registration.SchoolNotFoundError(f'No school found for index {index}.')
    return {'school_index': '914', 'school_name': 'Test School'}

bulk_registration.fetch_school = fetch_bulk_school
app=create_app()
if __name__=='__main__':
    uvicorn.run(app,host='127.0.0.1',port=8123)
