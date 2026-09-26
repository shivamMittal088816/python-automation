import { ClearMappingFileButton } from './ClearMappingFileButton';
import { EmptyState, LoadedFile, PageHeader } from './Presentation';
import { useEffect } from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { useSessionValue } from '../../hooks/useSessionValue';
import { useRequest } from '../../hooks/useRequest';
import { fileApi } from '../../services/fileApi';
import { admissionMappingApi } from '../../services/admissionMappingApi';
import { ActionLink, Alert, Button, Card, DownloadButton, Input, Loading, Metrics, Select } from './Controls';
import { DumpDownload } from './DumpDownload';
import { DataTable } from '../tables/DataTable';

export function FileViewer({ kind, title }) {
  const { id, workspace, run, busy } = useWorkspace(), saved = workspace.files[kind];
  if (!saved) return <div className="page-stack"><PageHeader title={title} description={kind === 'school' ? 'Explore your school file, search students, and view classes and sections.' : kind === 'dump' ? 'Browse existing student records and review the school overview.' : 'Search the student records found through email mapping.'} /><ActionLink to={kind === 'email_dump' ? '/email_mapping_page' : '/admission_file_page'}>{kind === 'email_dump' ? 'Back to email mapping' : 'Back to mapping'}</ActionLink><EmptyState title={kind === 'school' ? 'No school file loaded' : kind === 'dump' ? 'No student dump loaded' : 'No email dump loaded'}>{kind === 'school' ? 'Add a school file on the admission mapping page to view its students here.' : kind === 'dump' ? 'Select a dump file on the admission mapping page first.' : 'No email dump available. Fetch the email dump from Email mapping first.'}</EmptyState></div>;
  return <LoadedViewer key={`${id}-${kind}-${saved.version}`} {...{ kind, title, id, workspace, run, busy, saved }} />;
}

function ColumnPicker({ columns, value, onChange }) {
  const selected = new Set(value);
  const toggle = column => onChange(
    selected.has(column) ? value.filter(item => item !== column) : [...value, column],
  );

  return <div className="my-2">
    <details className="group overflow-hidden rounded-lg border border-slate-200 bg-white">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50" aria-labelledby="columns-to-search-label">
        <span className="flex min-w-0 items-center gap-2"><strong id="columns-to-search-label" className="font-medium">Columns to search</strong><span className="truncate text-xs text-slate-500">{value.length ? `${value.length} selected` : 'Choose columns'}</span></span>
        <span aria-hidden="true" className="text-slate-400 transition-transform group-open:rotate-180">⌄</span>
      </summary>
      <div className="border-t border-slate-200 bg-slate-50/60 p-2">
        <div className="mb-2 flex items-center justify-end gap-1">
          <button type="button" className="rounded-md px-2 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-50" onClick={() => onChange([...columns])}>Select all</button>
          <button type="button" className="rounded-md px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-200" onClick={() => onChange([])}>Clear</button>
        </div>
        <div role="group" aria-labelledby="columns-to-search-label" className="grid max-h-36 gap-1.5 overflow-y-auto pr-1 sm:grid-cols-3 lg:grid-cols-4">
          {columns.map(column => <label key={column} className={`flex cursor-pointer items-center gap-1.5 rounded-md border px-2 py-1.5 text-xs transition ${selected.has(column) ? 'border-blue-300 bg-blue-50 text-blue-900' : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'}`}>
            <input type="checkbox" className="h-3.5 w-3.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500" checked={selected.has(column)} onChange={() => toggle(column)} />
            <span className="min-w-0 truncate" title={column}>{column}</span>
          </label>)}
        </div>
      </div>
    </details>
  </div>;
}

function LoadedViewer({ kind, title, id, workspace, run, busy, saved }) {
  const key = `${id}-${kind}-${saved.version}-viewer`;
  const [query, setQuery] = useSessionValue(`${key}-search`, ''), [mode, setMode] = useSessionValue(`${key}-mode`, 'All columns'), [scope, setScope] = useSessionValue(`${key}-columns`, []);
  const [sheet, setSheet] = useSessionValue(`${key}-sheet`, (kind === 'school' ? workspace.settings.admission_school_sheet : workspace.settings.admission_dump_sheet) || saved.sheets[0] || '');
  const [page, setPage] = useSessionValue(`${key}-page`, 1), [size, setSize] = useSessionValue(`${key}-size`, 50);
  const [classColumn, setClass] = useSessionValue(`${key}-class`, workspace.settings.school_overview_class_column || ''), [sectionColumn, setSection] = useSessionValue(`${key}-section`, workspace.settings.school_overview_section_column || '');
  const [schoolIndex, setSchoolIndex] = useSessionValue(`${key}-index`, saved.school_index || ''), [schoolName, setSchoolName] = useSessionValue(`${key}-name`, saved.school_name || '');
  const selectedScope = mode === 'Selected columns' ? scope : null;
  const effectiveQuery = selectedScope?.length === 0 ? '' : query;
  const params = { sheet: sheet || undefined, query: effectiveQuery, columns: selectedScope, page,
    limit: size,
    class_column: kind === 'school' && classColumn !== sectionColumn ? classColumn || null : null,
    section_column: kind === 'school' && classColumn !== sectionColumn ? sectionColumn || null : null };
  const request = useRequest(signal => fileApi.table(kind, params, signal), [id, kind, JSON.stringify(params)]);
  const data = request.data;
  useEffect(() => {
    if (!data) return;
    if (kind === 'dump' && !schoolIndex && data.inferred_school_index) setSchoolIndex(data.inferred_school_index);
  }, [data]);
  function change(setter, value) { setter(value); setPage(1); }
  function overviewChange(key, setter, value) { change(setter, value); }
  return <div className={kind === 'school' ? 'space-y-4' : 'page-stack'}><PageHeader title={title} description={kind === 'school' ? 'A compact view of students grouped by the class and section labels in your file.' : kind === 'dump' ? 'Browse existing student records and review the school overview.' : 'Search the student records found through email mapping.'} /><div className="flex flex-wrap items-center gap-3"><ActionLink to={kind === 'dump' ? '/admission_preview_page' : kind === 'email_dump' ? '/email_mapping_page' : '/admission_file_page'}>{kind === 'dump' ? 'Back to preview' : kind === 'email_dump' ? 'Back to email mapping' : 'Back to mapping'}</ActionLink>{kind === 'school' ? <DownloadButton action={() => fileApi.download(kind)}>Download original</DownloadButton> : <details><summary className="text-sm font-medium">{kind === 'email_dump' ? 'Download email dump' : 'Download dump'}</summary><div className="mt-3"><DumpDownload kind={kind} /></div></details>}</div><div className="flex flex-wrap items-center justify-between gap-2"><LoadedFile name={saved.name} /><ClearMappingFileButton kind={kind} /></div>{kind === 'email_dump' && <p className="caption">Users found by input email addresses across schools. This is separate from the admission dump.</p>}{saved.sheets.length > 0 && <Select label={kind === 'school' ? 'Choose worksheet' : 'Sheet'} options={saved.sheets} value={sheet} onChange={event => change(setSheet, event.target.value)} />}{request.error && <Alert type="error">{request.error}</Alert>}
    {(kind === 'school' || kind === 'dump') && <Card className={kind === 'school' ? 'p-4 sm:p-4' : ''}><div className="mb-3 flex flex-wrap items-center justify-between gap-2"><div><h3 className="font-semibold">{kind === 'school' ? 'School statistics' : 'School overview'}</h3>{kind === 'school' && <p className="mt-1 text-xs text-slate-500">Unique classes, student totals and sections</p>}</div>{kind === 'school' && data?.overview && <div className="flex gap-2"><span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">{data.overview.length} classes</span><span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">{data.total.toLocaleString()} students</span></div>}</div>{kind === 'dump' ? <>{!saved.source?.startsWith('SQL school ') && <details open={!saved.school_index || !saved.school_name}><summary className="text-sm font-medium">Record school details</summary><form className="my-3 grid items-end gap-3 sm:grid-cols-[1fr_2fr_1fr]" onSubmit={event => { event.preventDefault(); run('Saving school details…', revision => admissionMappingApi.schoolDetails({ school_index: schoolIndex, school_name: schoolName }, revision)); }}><Input label="School index" value={schoolIndex} onChange={event => setSchoolIndex(event.target.value)} /><Input label="School name" value={schoolName} onChange={event => setSchoolName(event.target.value)} /><Button primary disabled={!!busy} type="submit">Save details</Button></form></details>}<Metrics items={[["School index", saved.school_index || data?.inferred_school_index || 'Not provided'], ["School name", saved.school_name || 'Not provided'], ["Dump records", data?.total], ["Students", data?.student_count ?? data?.total]]} />{data?.overview ? <><p className="my-3 caption">Numeric dump classes are displayed as user_edu_class + 1 (for example, 5 → Class 6).</p><DataTable rows={data.overview} /></> : data && <Alert>Add user_edu_class and user_edu_major columns to see the class and section breakdown.</Alert>}</> : <>{data && <div className="mb-3 grid gap-2 sm:grid-cols-2"><Select label="Class column" options={[{ value: '', label: 'Choose class column' }, ...data.columns]} value={classColumn} onChange={event => overviewChange('school_overview_class_column', setClass, event.target.value)} /><Select label="Section column" options={[{ value: '', label: 'Choose section column' }, ...data.columns]} value={sectionColumn} onChange={event => overviewChange('school_overview_section_column', setSection, event.target.value)} /></div>}{classColumn && classColumn === sectionColumn ? <Alert type="warning">Choose different class and section columns.</Alert> : data?.overview ? <><p className="mb-2 text-xs text-slate-500">Class and section values are displayed exactly as provided in the school file.</p><DataTable rows={data.overview} /></> : <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-center text-sm text-slate-500">Select the class and section columns to build the statistics table.</div>}</>}</Card>}
    <Card className={kind === 'school' || kind === 'dump' ? 'p-4 sm:p-4' : ''}><div className="mb-3 flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold">{kind === 'dump' || kind === 'school' ? 'Find a student' : 'Search records'}</h3><fieldset><legend className="sr-only">Search in</legend><div className="flex gap-3 rounded-lg bg-slate-100 p-1">{['All columns', 'Selected columns'].map(option => <label key={option} className={`cursor-pointer rounded-md px-2 py-1 text-xs font-medium ${mode === option ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'}`}><input type="radio" name={`${kind}-scope`} className="sr-only" checked={mode === option} onChange={() => change(setMode, option)} />{option}</label>)}</div></fieldset></div>{mode === 'Selected columns' && <ColumnPicker columns={data?.columns || []} value={scope} onChange={columns => change(setScope, columns)} />}<div className="grid gap-2 sm:grid-cols-[3fr_1fr]"><Input label={kind === 'email_dump' ? 'Search email dump' : mode === 'All columns' ? 'Search all columns' : 'Search selected columns'} value={query} disabled={mode === 'Selected columns' && !scope.length} placeholder={kind === 'email_dump' ? 'Email, name, user ID or school index' : kind === 'dump' ? 'Admission number, name, email or user ID' : 'Name, admission number or other value'} onChange={event => change(setQuery, event.target.value)} /><Select label="Rows per page" options={[25, 50, 100]} value={size} onChange={event => change(setSize, Number(event.target.value))} /></div>{mode === 'Selected columns' && !scope.length && <p className="mt-2 caption">Choose columns to start searching.</p>}</Card>{request.loading && <Loading>Reading file…</Loading>}{data && <><div className="flex flex-wrap items-end justify-between gap-2"><p className="text-sm font-semibold">{kind === 'school' ? 'School students' : kind === 'email_dump' ? 'Email dump records' : 'Student records'} · {data.found.toLocaleString()} of {data.total.toLocaleString()}</p><Input label="Page" type="number" min={1} max={data.pages} value={data.page} onChange={event => setPage(Math.max(1, Math.min(data.pages, Number(event.target.value) || 1)))} /></div><p className="text-xs text-slate-500">Page {data.page} of {data.pages}</p><DataTable rows={data.rows} columns={data.columns} highlight={effectiveQuery} scope={selectedScope} />{data.found === 0 && <Alert>{kind === 'email_dump' ? 'No records found.' : kind === 'dump' ? 'No students found. Try another search.' : 'No students found.'}</Alert>}</>}</div>;
}
