"""File downloads endpoints for the mapping API."""
from Backend.api.session_cookie import SessionId
from pathlib import Path
import logging
import re
from urllib.parse import quote
from fastapi import APIRouter
from fastapi.responses import Response
from Backend.api.file_workflow_state import workspace
from Backend.utils.workbook_operations import convert_dump
from Backend.api.file_workflow_constants import FILES, STAGES
from Backend.api.file_workflow_validation import fail
from Backend.api.file_workflow_snapshots import read_snapshot


router = APIRouter(tags=['File downloads'])
logger = logging.getLogger('uvicorn.error')


@router.get('/downloads/{kind}')
def download(session_id: SessionId,kind: str,filename: str | None=None,format: str | None=None,sheet: str | None=None):
    with workspace(session_id,persist=False) as state:
        if kind in STAGES:
            snapshot=state.get(STAGES[kind],{}).get(filename)
            if not snapshot:
                fail('Result group not found.',404)
            name=filename
            data=snapshot['data']
            if format=='csv':
                data=read_snapshot({'name':filename,'data':data}).to_csv(index=False).encode('utf-8-sig')
                name=Path(filename).with_suffix('.csv').name
            elif format not in (None,'xlsx'):
                fail('Choose CSV or XLSX format.')
        else:
            if kind not in FILES or not state.get(FILES[kind]):
                fail('No file available.',404)
            snapshot=state[FILES[kind]]
            name,data=snapshot['name'],snapshot['data']
            if kind!='school' and format:
                if format not in ('csv','xlsx'):
                    fail('Choose CSV or XLSX format.')
                try:
                    data=convert_dump(data,name,format,sheet if sheet is not None else 0)
                except Exception:
                    logger.exception('Failed to convert a dump download.')
                    fail('Could not prepare the dump download. Check that the file is a valid CSV or XLSX.')
                stem=Path(name).stem
                school=state.get('saved_admission_dump',{})
                if school.get('school_index') and school.get('school_name'):
                    label=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',f"{school['school_index']}-{school['school_name']}")
                    stem=f"{label}({'email_dump_file' if kind=='email_dump' else 'dump_file'})"
                name=f'{stem}.{format}'
        mime='text/csv' if name.lower().endswith('.csv') else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return Response(data,media_type=mime,headers={'Content-Disposition':f"attachment; filename*=UTF-8''{quote(name)}"})
