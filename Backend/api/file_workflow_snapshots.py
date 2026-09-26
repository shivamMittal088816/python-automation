"""Read uploaded snapshots, select worksheets and register input files."""
from io import BytesIO
from pathlib import Path
import tempfile
import logging
import pandas as pd
from Backend.api.file_workflow_constants import FILES
from Backend.api.file_workflow_validation import fail
from Backend.services.admission_mapping.admission_file_mapping import read_file


ROOT = Path(__file__).resolve().parents[2]
logger = logging.getLogger('uvicorn.error')


def read_snapshot(snapshot, sheet=None):
    folder = ROOT / 'storage' / 'temp' / 'admission_mapping'
    folder.mkdir(parents=True, exist_ok=True)
    path = None
    try:
        with tempfile.NamedTemporaryFile(dir=folder, suffix=Path(snapshot['name']).suffix.lower(), delete=False) as file:
            path = Path(file.name)
            file.write(snapshot['data'])
        try:
            return read_file(path, sheet)
        except Exception:
            logger.exception('Failed to parse a saved mapping file.')
            fail('Could not read this file. Check that it is a valid CSV or XLSX file.')
    finally:
        if path is not None:
            path.unlink(missing_ok=True)


def sheets(snapshot):
    if Path(snapshot['name']).suffix.lower() == '.xlsx':
        try:
            with pd.ExcelFile(BytesIO(snapshot['data'])) as workbook:
                return workbook.sheet_names
        except (ValueError, OSError, ImportError):
            return []
    return []


def selected_sheet(state, kind, requested=None):
    saved = state[FILES[kind]]
    names = sheets(saved)
    preferred = requested if requested is not None else state.get('admission_settings', {}).get(
        'admission_school_sheet' if kind == 'school' else 'admission_dump_sheet')
    return preferred if preferred in names else names[0] if names else None


def add_snapshot(state,kind,name,data,**metadata):
    if kind not in ('school','dump'):
        fail('Unknown input file.')
    if Path(name).suffix.lower() not in ('.csv','.xlsx'):
        fail('Enter a CSV or XLSX file path.')
    state[FILES[kind]]={'name':Path(name).name,'data':data,'source':name,**metadata}
