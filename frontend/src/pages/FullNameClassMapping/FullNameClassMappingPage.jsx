import { RunColumns } from '../../components/common/RunColumns';
import { PageHeader } from '../../components/common/Presentation';
import { useWorkspace } from '../../context/WorkspaceContext';
import { useSessionValue } from '../../hooks/useSessionValue';
import { useRequest } from '../../hooks/useRequest';
import { emailMappingApi } from '../../services/emailMappingApi';
import { Alert, Button, Card, Loading, Select } from '../../components/common/Controls';
import { MappingResultCards } from '../../components/common/MappingResultCards';

export function FullNameClassMappingPage() {
  const { workspace } = useWorkspace();
  return <div className="page-stack">
    <PageHeader title="Full name + class Number" description="Choose a student source and match using full name and class number." />
    {!workspace.files.school ? <Alert>Load a school file first.</Alert> : !workspace.files.dump ? <Alert>Load the admission dump first.</Alert> : <FullNameForm />}
    {Object.keys(workspace.exports.full_name_class).length > 0 && <MappingResultCards stage="full_name_class" previewPath="/full_name_class_preview_page" title="Mapping results" />}
  </div>;
}

function FullNameForm() {
  const { workspace, busy, clearNotice } = useWorkspace();
  const [selected, setSelected] = useSessionValue(`${workspace.workspace_id}:class-source:${workspace.files.school.version}:${workspace.settings.admission_school_sheet}`, null);
  const source = selected || workspace.settings.full_name_class_input_source || 'school_file';
  const sources = [
    ['school_file', 'School file'],
    ['admission_not_matched', 'Admission mapping — Not matched'],
    ['email_not_matched', 'Email mapping — Not matched'],
  ];
  const version = source === 'school_file' ? workspace.files.school.version
    : source === 'admission_not_matched' ? workspace.export_versions?.admission?.['not_matched.xlsx']
    : workspace.export_versions?.email?.['email_not_matched.xlsx'];
  return <Card>
    <fieldset disabled={!!busy}>
      <legend className="mb-3 text-sm font-semibold">Class mapping input</legend>
      <div className="grid gap-3 sm:grid-cols-3">
        {sources.map(([value, label]) => <label key={value} className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${source === value ? 'border-blue-400 bg-blue-50 text-blue-900' : 'border-slate-200'}`}>
          <input type="radio" name="class-mapping-source" value={value} checked={source === value} onChange={() => { clearNotice(); setSelected(value); }} />
          {label}
        </label>)}
      </div>
    </fieldset>
    <div className="mt-4">
      {version ? <SourceFields key={`${workspace.workspace_id}:${workspace.files.school.version}`} source={source} />
        : <Alert>Run {source === 'admission_not_matched' ? 'Admission' : 'Email'} mapping first to use its Not matched students.</Alert>}
    </div>
  </Card>;
}

function SourceFields({ source }) {
  const { id, workspace, run, busy, metadataKeys, getMappingMetadata } = useWorkspace();
  const request = useRequest(() => getMappingMetadata('school'), [metadataKeys.school]);
  const dump = useRequest(() => getMappingMetadata('dump'), [metadataKeys.dump]);
  const [draft, setDraft] = useSessionValue(`${id}:class-draft:${workspace.files.school.version}:${workspace.settings.admission_school_sheet}`, {});
  const columns = request.data?.columns || [], values = { ...workspace.settings, ...draft };
  const total = source === 'school_file' ? request.data?.total
    : source === 'admission_not_matched' ? workspace.exports.admission['not_matched.xlsx']
    : workspace.exports.email['email_not_matched.xlsx'];
  const normalized = value => String(value).toLowerCase().replace(/[^a-z0-9]/g, '');
  const suggestedName = request.data?.suggestions?.full_name_column || columns.find(column => ['fullname', 'studentname', 'name'].includes(normalized(column)));
  const suggestedClass = request.data?.suggestions?.class_number_column || columns.find(column => ['classnumber', 'class', 'grade'].includes(normalized(column)));
  const name = values.full_name_class_name_column === '' ? '' : columns.includes(values.full_name_class_name_column) ? values.full_name_class_name_column : suggestedName || '';
  const classColumn = values.full_name_class_class_column === '' ? '' : columns.includes(values.full_name_class_class_column) ? values.full_name_class_class_column : suggestedClass || '';
  const update = settings => setDraft(previous => ({ ...previous, ...settings }));
  if (request.loading || dump.loading) return <Loading>Reading selected files…</Loading>;
  if (request.error || dump.error) return <Alert type="error">{request.error || dump.error}</Alert>;
  if (!dump.data.has_generated_col) return <Alert type="error">The admission dump has no generated_col column.</Alert>;
  if (!total) return <Alert>The selected source has no students to map.</Alert>;
  return <>
    <section className="rounded-xl border border-blue-200 bg-blue-50/50 p-4">
      <h3 className="text-sm font-semibold text-blue-900">Class concatenation <RunColumns stage="full_name_class" pass="1" /></h3>
      <p className="mb-3 mt-2 text-sm leading-5 text-slate-600">Loaded {total.toLocaleString()} students from the selected source. Choose full name and class columns from the school file headers.</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <Select label="Full name" options={[{ value: '', label: 'Choose a full name column' }, ...columns]} value={name} disabled={!!busy} onChange={event => update({ full_name_class_name_column: event.target.value })} />
        <Select label="Class Number" options={[{ value: '', label: 'Choose a class column' }, ...columns]} value={classColumn} disabled={!!busy} onChange={event => update({ full_name_class_class_column: event.target.value })} />
      </div>
      <div className="mt-3"><Button primary disabled={!!busy || !name || !classColumn} onClick={() => run('Running class concatenation mapping...', () => emailMappingApi.fullNameClass(id, {
        name_column: name,
        class_column: classColumn,
        source,
      }))}>Run mapping</Button></div>
    </section>
  </>;
}
