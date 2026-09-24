"""Browser-test server: actual services/API with fixture repositories, isolated disk storage."""
import atexit
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0,str(ROOT))
import pandas as pd
import uvicorn
from Backend.api import file_workflow_state
from Backend.routes.file_workflow_routes import email_mapping, file_inputs
from Backend.main import create_app
from Backend import main as backend_main

# This server uses fixture repositories, including a simulated startup DB check.
# The real connectivity check and its failure logging have separate unit coverage.
backend_main.check_database_connection = lambda: None

temporary=tempfile.TemporaryDirectory(prefix='student-mapping-browser-')
atexit.register(temporary.cleanup)
file_workflow_state.ROOT=Path(temporary.name)/'sessions'
dump=pd.read_csv(ROOT/'frontend/e2e/fixtures/dump.csv',dtype=str,keep_default_na=False)

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

app=create_app()
if __name__=='__main__':
    uvicorn.run(app,host='127.0.0.1',port=8123)
