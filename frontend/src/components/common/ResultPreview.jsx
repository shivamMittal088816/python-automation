import { useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router';
import { useWorkspace } from '../../context/WorkspaceContext';
import { useSessionValue } from '../../hooks/useSessionValue';
import { useRequest } from '../../hooks/useRequest';
import { admissionMappingApi } from '../../services/admissionMappingApi';
import { fileApi } from '../../services/fileApi';
import { Alert, Button, Card, DownloadButton, Input, Loading, Metrics, Select } from './Controls';
import { DataTable } from '../tables/DataTable';
export function ResultPreview({ stage, label = 'Choose result group' }) {
  const { workspace, id } = useWorkspace(), counts = workspace.exports[stage];
  const [params, setParams] = useSearchParams();
  const names = Object.keys(counts);
  const key = `${id}-${stage}`;
  const [savedFilename, setFilename] = useSessionValue(`${key}-group`, params.get('file') || names[0]);
  const requested = params.get('file');
  const filename = names.includes(requested) ? requested : names.includes(savedFilename) ? savedFilename : names[0];
  const [page, setPage] = useSessionValue(`${key}-${filename}-${workspace.export_versions[stage]?.[filename]}-page`, 1), [size, setSize] = useSessionValue(`${key}-size`, 50);
  const signature = JSON.stringify(workspace.export_versions[stage]);
  const request = useRequest(signal => admissionMappingApi.results(stage, filename, { page, limit: size }, signal), [id, stage, filename, page, size, signature]);
  const data = request.data;
  const previousFilename = useRef(filename);
  useEffect(() => {
    if (previousFilename.current !== filename) setPage(1);
    previousFilename.current = filename;
    if (savedFilename !== filename) setFilename(filename);
  }, [filename, savedFilename, setFilename, setPage]);
  const groupLabel = name => name.includes('not_matched') ? 'Not matched' : name.includes('review') ? 'Review' : 'Matched';
  return <div className="space-y-4"><div><h3 className="font-semibold text-slate-900">Saved mapping results</h3><p className="mt-1 caption">Results from your last run. Opening this page does not run mapping again.</p></div><p className="caption">Student previews are locked. You can view and download results; students cannot be moved between result groups.</p><Metrics items={names.map(name => [groupLabel(name), counts[name]])} /><Card><div className="flex flex-wrap items-end gap-3"><Select label={label} options={names.map(name => ({ value: name, label: `${groupLabel(name)} (${counts[name].toLocaleString()})` }))} value={filename} onChange={event => { setFilename(event.target.value); setPage(1); setParams(previous => { previous.set('file', event.target.value); return previous; }, { replace: true }); }} />{names.length > 0 && <><DownloadButton action={() => fileApi.download(stage, { filename, format: 'xlsx' })}>Download Excel</DownloadButton><DownloadButton action={() => fileApi.download(stage, { filename, format: 'csv' })}>Download CSV</DownloadButton></>}</div></Card>{request.loading && <Loading>Reading result workbook…</Loading>}{request.error && <Alert type="error">{request.error}</Alert>}{data && data.found === 0 ? <Alert>This result group has no students. The download contains column headers only.</Alert> : data && <><div className="flex flex-wrap items-end gap-3"><Select label="Rows per page" options={[25, 50, 100]} value={size} onChange={event => { setSize(Number(event.target.value)); setPage(1); }} /><Button disabled={data.page === 1} onClick={() => setPage(data.page - 1)}>Previous</Button><Input label="Page" type="number" min={1} max={data.pages} value={data.page} onChange={event => setPage(Math.max(1, Math.min(data.pages, Number(event.target.value) || 1)))} /><Button disabled={data.page === data.pages} onClick={() => setPage(data.page + 1)}>Next</Button></div><p className="caption">{ `Rows ${data.offset + 1}–${data.end} of ${data.found.toLocaleString()} · Page ${data.page} of ${data.pages} · Downloads include all records.`}</p>{stage === 'admission' && <p className="caption">School columns keep their original file headers. Columns starting with dump_ contain dump values or lookup details; comparison fields contain values used by mapping.</p>}<DataTable rows={data.rows} columns={data.columns} labels={data.column_labels} offset={data.offset} /></>}</div>;
}
