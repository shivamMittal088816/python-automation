"""Stream rollback database dumps to CSV and XLSX files."""

import csv
from itertools import chain
import os
from pathlib import Path
import tempfile

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell

from app.services import rollback as rollback_storage


def safe_csv_cell(value):
    text_value = '' if value is None else str(value)
    if text_value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')):
        return "'" + text_value
    return text_value


def export_dump_file(workspace_id, file_format):
    descriptor, name = tempfile.mkstemp(
        prefix='rollback-dump-', suffix=f'.{file_format}',
    )
    os.close(descriptor)
    target = Path(name)
    try:
        with rollback_storage.open_dump_rows(workspace_id) as (columns, rows, _):
            if file_format == 'csv':
                with target.open('w', encoding='utf-8-sig', newline='') as output:
                    writer = csv.writer(output, lineterminator='\n')
                    writer.writerow([safe_csv_cell(value) for value in columns])
                    for row in rows:
                        writer.writerow([safe_csv_cell(value) for value in row])
            else:
                workbook = Workbook(write_only=True)
                sheet = workbook.create_sheet('Rollback dump')
                sheet.freeze_panes = 'A2'
                for row in chain([columns], rows):
                    cells = []
                    for value in row:
                        cell = WriteOnlyCell(
                            sheet, value='' if value is None else str(value),
                        )
                        cell.data_type = 's'
                        cells.append(cell)
                    sheet.append(cells)
                workbook.save(target)
        return target
    except Exception:
        target.unlink(missing_ok=True)
        raise
