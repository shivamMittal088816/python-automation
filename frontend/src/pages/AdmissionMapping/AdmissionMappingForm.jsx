import { RunColumns } from '../../components/common/RunColumns';
import { useEffect, useState } from 'react';
import { useSessionValue } from '../../hooks/useSessionValue';
import { useWorkspace } from '../../context/WorkspaceContext';
import { admissionMappingApi } from '../../services/admissionMappingApi';
import { FileInput } from '../../components/common/FileInput';
import { DumpDownload } from '../../components/common/DumpDownload';
import { ActionLink, Alert, Button, Card, Input, Metrics, Select } from '../../components/common/Controls';
import { Badge, LoadedFile, PageHeader, SectionHeader, Stepper } from '../../components/common/Presentation';
export function AdmissionMappingForm() {
  const { workspace, id, busy, run } = useWorkspace();
  const [draft, setDraft] = useSessionValue(`${id}:admission-draft:${workspace.files.school?.version}:${workspace.files.dump?.version}`, {});
  const [preview, setPreview] = useState(null);
  const [previewBusy, setPreviewBusy] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const values = { ...workspace.settings, ...draft };
  const config = preview?.configuration || workspace.configuration;
  const selection = () => Object.fromEntries(['admission_school_sheet', 'admission_dump_sheet', 'school_admission_col', 'school_name_col'].map(key => [key, values[key]]));
  useEffect(() => { setPreview(null); setPreviewBusy(false); setPreviewError(''); }, [id, workspace.files.school?.version, workspace.files.dump?.version]);
  useEffect(() => {
    if (draft.admission_school_sheet === undefined && draft.admission_dump_sheet === undefined) return;
    const controller = new AbortController();
    setPreviewBusy(true); setPreviewError('');
    admissionMappingApi.configuration(id, selection(), controller.signal).then(data => {
      if (controller.signal.aborted) return;
      setPreview(data);
      setDraft(previous => ({ ...previous, school_admission_col: data.settings.school_admission_col, school_name_col: data.settings.school_name_col }));
    }).catch(error => { if (!controller.signal.aborted) setPreviewError(error.message); })
      .finally(() => { if (!controller.signal.aborted) setPreviewBusy(false); });
    return () => controller.abort();
  }, [id, draft.admission_school_sheet, draft.admission_dump_sheet, workspace.files.school?.version, workspace.files.dump?.version]);
  const sqlDump = workspace.files.dump?.source?.startsWith('SQL school ');
  const savedSchoolIndex = (sqlDump && workspace.files.dump.school_index) || values.admission_dump_school_index || '';
  const [schoolIndex, setSchoolIndex] = useState(savedSchoolIndex);
  useEffect(() => { setSchoolIndex(savedSchoolIndex); }, [id, savedSchoolIndex]);
  const [source, setSource] = useSessionValue(`${id}:dump-source:${workspace.files.dump?.version}`, sqlDump ? 'Fetch from SQL' : values.admission_dump_source || 'Upload dump file');
  const changeSource = setSource;
  const update = settings => setDraft(previous => ({ ...previous, ...settings }));
  return <div className="page-stack"><PageHeader title="Admission File Mapping" description="Map school records against the existing student database." /><Stepper active={Object.keys(workspace.exports.admission).length ? 2 : config ? 1 : 0} /><div className="grid items-start gap-4 lg:grid-cols-2"><Card><SectionHeader step="01" title="School file" description="The students you want to map." /><FileInput kind="school" label="school" /></Card><Card className="dump-panel"><SectionHeader step="01" title="Student dump" description="The existing student records to match against." /><fieldset className="mb-4"><legend className="mb-2 text-sm font-medium">Dump source</legend><div className="grid gap-2 sm:grid-cols-2">{['Fetch from SQL', 'Upload dump file'].map(option => <label key={option} className={`rounded-lg border px-3 py-3 text-sm transition-colors ${source === option ? 'border-blue-300 bg-blue-50 text-blue-900' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}><input disabled={!!busy} type="radio" aria-label={option} name="dump-source" value={option} checked={source === option} onChange={() => changeSource(option)} className="mr-2" />{option}<span aria-hidden="true" className="mt-1 block pl-6 text-xs leading-5 text-slate-500">{option === 'Fetch from SQL' ? 'Load records by school index' : 'Use a CSV or XLSX file'}</span></label>)}</div></fieldset>{source === 'Upload dump file' ? <><FileInput kind="dump" label="dump" />{workspace.files.dump && <UploadedDumpSchoolIndex key={workspace.files.dump.version} />}</> : <div className="space-y-3"><form className="dump-fetch flex flex-wrap items-end gap-3" onSubmit={async event => { event.preventDefault(); await run('Fetching dump data…', () => admissionMappingApi.fetchDump(id, schoolIndex)); }}><Input label="School index" value={schoolIndex} onChange={event => { setSchoolIndex(event.target.value); }} placeholder="Enter school index" /><Button className="dump-fetch-button" primary disabled={!!busy} type="submit">Fetch dump data</Button></form>{workspace.files.dump && <div className="dump-loaded" role="status"><LoadedFile name={workspace.files.dump.name} /></div>}</div>}{workspace.files.dump && <div className="dump-school mt-3"><div className="dump-actions"><ActionLink to="/dump_file_page">View school overview <span aria-hidden="true">?</span></ActionLink><details><summary className="text-sm font-semibold">Download dump</summary><div className="mt-3"><DumpDownload /></div></details></div></div>}</Card></div><p className="caption">Selections are saved when you run mapping. Refreshing discards unfinished changes.</p>{previewError && <Alert type="error">{previewError}</Alert>}{workspace.configuration_error && <Alert type="error">{workspace.configuration_error}</Alert>}{config && <><Card className="mapping-settings"><SectionHeader step="02" title="Mapping settings" description="Choose the school columns used to match student records." /><div className="mapping-fields">{config.school_sheets.length > 0 && <Select label="School sheet" options={config.school_sheets} value={values.admission_school_sheet} disabled={!!busy} onChange={event => update({ admission_school_sheet: event.target.value })} />}{config.dump_sheets.length > 0 && <Select label="Dump sheet" options={config.dump_sheets} value={values.admission_dump_sheet} disabled={!!busy} onChange={event => update({ admission_dump_sheet: event.target.value })} />}<Select label="School admission number column" options={config.school_columns} value={values.school_admission_col} disabled={!!busy} onChange={event => update({ school_admission_col: event.target.value })} />{config.missing_columns.length === 0 && <Select label="First name column in school file" options={config.school_columns} value={values.school_name_col} disabled={!!busy} onChange={event => update({ school_name_col: event.target.value })} />}</div>{config.missing_columns.length > 0 ? <Alert type="error">Dump file is missing required columns: {config.missing_columns.join(', ')}</Alert> : <><p className="my-3 caption">Dump columns: {config.dump_admission} for admission lookup, {config.dump_first_name} for lowercase first-name comparison, and {config.username} for the returned username.</p><p className="caption">Last loaded configuration: admission lookup: {config.admission_hits.toLocaleString()} of {config.school_rows.toLocaleString()} school rows found in the dump.</p>{config.school_rows > 0 && config.admission_hits === 0 && <Alert type="warning">No admission numbers match. Check the school admission number column, selected sheets, and school index before mapping.</Alert>}</>}</Card><div className="grid gap-3 lg:grid-cols-2">
  <section className="min-w-0 rounded-xl border border-blue-200 bg-blue-50/50 p-4">
    <h3 className="text-sm font-semibold text-blue-900">Admission number + first name <RunColumns stage="admission" pass="1" /></h3>
    <p className="my-3 text-sm leading-5 text-slate-600">Match school admission numbers against the dump and compare first names. Results are grouped into Matched, Review, and Not matched.</p>
    <Button primary disabled={!!busy || previewBusy || !!previewError || config.missing_columns.length > 0 || !workspace.files.dump?.school_index} onClick={() => run('Mapping students...', () => admissionMappingApi.map(id, selection()))}>Run mapping</Button>
  </section>
</div></>}{Object.keys(workspace.exports.admission).length > 0 && <><SectionHeader step="03" title="Mapping results" description="Saved results from your last run. Select Run mapping to run again." /><Metrics items={[["Rows in identical duplicate groups", config?.duplicate_rows], ["Duplicate rows dropped", config?.dropped_rows]]} /><p className="caption">One copy of each completely identical school row is kept before admission mapping.</p><div className="grid gap-3 sm:grid-cols-3">{[['matched.xlsx', 'Matched', 'Admission number matches uniquely with a matching first name; returns the dump username and user ID.'], ['review.xlsx', 'Review', 'Admission number is blank, duplicated in the school file, or occurs more than once in the dump; or the name comparison failed or a name is missing. Dump row numbers include the header as row 1.'], ['not_matched.xlsx', 'Not matched', 'Admission number not found in the dump.']].map(([name, label, description]) => <Card key={name}><Badge>{label}</Badge><p className="my-2 text-2xl font-semibold">{workspace.exports.admission[name]}</p><p className="mb-3 caption">{description}</p><ActionLink to={`/admission_preview_page?file=${name}`}>Preview {label.toLowerCase()}</ActionLink></Card>)}</div></>}</div>;
}

function UploadedDumpSchoolIndex() {
  const { workspace, id, busy, run } = useWorkspace();
  const saved = workspace.files.dump.school_index || '';
  const [index, setIndex] = useState(saved);
  return <form className="mt-3 space-y-3" onSubmit={event => {
    event.preventDefault();
    run('Saving school index...', () => admissionMappingApi.schoolDetails(id, { school_index: index.trim() }));
  }}>
    <Input label="School index" value={index} required inputMode="numeric" pattern="[0-9]+" disabled={!!busy} onChange={event => setIndex(event.target.value)} placeholder="Enter the school index for this dump" />
    <Button primary type="submit" disabled={!!busy || !/^[0-9]+$/.test(index.trim())}>Save school index</Button>
    {saved ? <p className="caption">Saved school index: {saved}</p> : <Alert>Enter and save the school index before starting mapping. Email mapping uses it to verify the student's school.</Alert>}
    {saved && index.trim() !== saved && <Alert>Save your changed school index before mapping.</Alert>}
  </form>;
}
