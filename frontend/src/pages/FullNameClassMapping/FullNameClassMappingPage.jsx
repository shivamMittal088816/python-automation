import { RunColumns } from '../../components/common/RunColumns';
import { PageHeader, SectionHeader } from '../../components/common/Presentation';
import { useWorkspace } from '../../context/WorkspaceContext';
import { useState } from 'react';
import { useRequest } from '../../hooks/useRequest';
import { emailMappingApi } from '../../services/emailMappingApi';
import { Alert, Button, Card, Loading, Select } from '../../components/common/Controls';
import { ResultPreview } from '../../components/common/ResultPreview';
const SOURCES = ['Admission mapping — Not matched', 'Email mapping — Not matched'];
export function FullNameClassMappingPage() {
  const { id, workspace, run } = useWorkspace();
  const counts = [workspace.exports.admission['not_matched.xlsx'] || 0, workspace.exports.email['email_not_matched.xlsx'] || 0];
  const [source, setSource] = useState( SOURCES.includes(workspace.settings.full_name_class_source) ? workspace.settings.full_name_class_source : counts[1] ? SOURCES[1] : SOURCES[0]);
  const available = Object.keys(source === SOURCES[0] ? workspace.exports.admission : workspace.exports.email).some(name => name.includes('not_matched'));
  if (!Object.keys(workspace.exports.admission).length) return <div className="page-stack"><PageHeader title="Full name + class Number" description="Match remaining students using their full name and class number." /><Alert>First run admission mapping.</Alert></div>;
  return <div className="page-stack"><PageHeader title="Full name + class Number" description="Match remaining students using their full name and class number." /><Card><SectionHeader title="Choose your input file" description="Select one Not matched result to continue mapping." /><fieldset><legend className="sr-only">Not matched source</legend><div className="flex flex-wrap gap-3">{SOURCES.map((label, index) => <label key={label} className={`rounded-lg border px-4 py-3 text-sm ${source === label ? 'border-blue-300 bg-blue-50 text-blue-900' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}><input type="radio" name="full-name-source" checked={source === label} onChange={() => setSource(label)} className="mr-2" />{label} ({counts[index].toLocaleString()} students)</label>)}</div></fieldset></Card>{!workspace.files.dump ? <Alert>Load the admission dump first.</Alert> : !available ? <Alert>{source} is not available yet. Choose the other file or complete this mapping first.</Alert> : <FullNameForm key={source} source={source} otherCount={counts[source === SOURCES[0] ? 1 : 0]} onOther={() => setSource(source === SOURCES[0] ? SOURCES[1] : SOURCES[0])} />}{Object.keys(workspace.exports.full_name_class).length > 0 && <><p className="caption">Results after round {workspace.full_name_class_round} · Blank admission numbers are allowed. One match: Matched · Multiple matches or duplicate username/user ID across mapping results: Review · No match: Not matched</p><ResultPreview stage="full_name_class" label="Result group" /></>}</div>;
}
function FullNameForm({ source, otherCount, onOther }) {
  const { id, workspace, run, busy, metadataKeys, getMappingMetadata } = useWorkspace();
  const kind = source === SOURCES[0] ? 'admission_source' : 'email_source';
  const request = useRequest(() => getMappingMetadata(kind), [kind, metadataKeys[kind]]);
  const dump = useRequest(() => getMappingMetadata('dump'), [metadataKeys.dump]);
  const [draft, setDraft] = useState({});
  const columns = request.data?.columns || [], values = { ...workspace.settings, ...draft };
  const preferred = source === SOURCES[1] ? values.email_full_name_column : values.school_name_col;
  const name = columns.includes(values.full_name_class_name_column) ? values.full_name_class_name_column : request.data?.suggestions.full_name_column || (columns.includes(preferred) ? preferred : columns[0]);
  const classColumn = columns.includes(values.full_name_class_class_column) ? values.full_name_class_class_column : request.data?.suggestions.class_number_column;
  const [savedSchoolName, setSchoolName] = useState( values.full_name_class_round_two_name_column || null);
  const [savedSchoolClass, setSchoolClass] = useState( values.full_name_class_round_two_class_column || null);
  const roundTwoName = savedSchoolName === '' || columns.includes(savedSchoolName) ? savedSchoolName : name;
  const roundTwoClass = savedSchoolClass === '' || columns.includes(savedSchoolClass) ? savedSchoolClass : classColumn;
  const firstRoundReady = workspace.full_name_class_round > 0;
  const update = settings => setDraft(previous => ({ ...previous, ...settings }));
  if (request.loading || dump.loading) return <Loading>Reading selected file…</Loading>;
  if (request.error || dump.error) return <Alert type="error">{request.error || dump.error}</Alert>;
  if (!dump.data.has_generated_col) return <Alert type="error">The admission dump has no generated_col column.</Alert>;
  if (!request.data.total) return <Card><h3 className="mb-2 font-semibold">No students in this file</h3><p className="mb-3">{source} has no students to map. Select the other Not matched file above if it has students.</p>{otherCount > 0 && <Button onClick={onOther}>Use {source === SOURCES[0] ? SOURCES[1] : SOURCES[0]}</Button>}</Card>;
  return <>
    <Card className="concat-passes">
      <div className="grid gap-3 lg:grid-cols-2">
        <section className="flex min-w-0 flex-col rounded-xl border border-blue-200 bg-blue-50/50 p-4">
          <h3 className="text-sm font-semibold text-blue-900">Pass 1: Class concatenation <RunColumns stage="full_name_class" pass="1" /></h3>
          <p className="mb-3 mt-2 text-sm leading-5 text-slate-600">Compare the school full name and class number with the dump's concatenated value.</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <Select label="Full name" options={columns} value={name} disabled={!!busy} onChange={event => update({ full_name_class_name_column: event.target.value })} />
            <Select label="Class Number" options={columns} value={classColumn} disabled={!!busy} onChange={event => update({ full_name_class_class_column: event.target.value })} />
          </div>
          <div className="mt-3"><Button primary disabled={!!busy || !name || !classColumn} onClick={() => run('Running 1st round mapping...', () => emailMappingApi.fullNameClass(id, source, name, classColumn))}>Run pass 1</Button></div>
        </section>
        <section className="flex min-w-0 flex-col rounded-xl border border-indigo-200 bg-indigo-50/50 p-4">
          <h3 className="text-sm font-semibold text-indigo-900">Pass 2: Sorted name + class <RunColumns stage="full_name_class" pass="2" /></h3>
          <p className="mb-3 mt-2 text-sm leading-5 text-slate-600">Retry pass 1's Not matched records. Ignore case and spaces, sort name characters, and compare class numbers.</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <Select label="School full name" options={[{ value: '', label: 'Choose a column' }, ...columns]} value={roundTwoName} disabled={!!busy} onChange={event => setSchoolName(event.target.value)} />
            <Select label="School Class Number" options={[{ value: '', label: 'Choose a column' }, ...columns]} value={roundTwoClass} disabled={!!busy} onChange={event => setSchoolClass(event.target.value)} />
          </div>
          <div className="mt-3"><Button disabled={!!busy || !firstRoundReady || !workspace.full_name_class_round_one_not_matched || !roundTwoName || !roundTwoClass} onClick={() => run('Running 2nd round mapping...', () => emailMappingApi.fullNameClass(id, source, roundTwoName, roundTwoClass, { round: 2 }))}>Run pass 2</Button></div>
          <p className="mt-2 text-xs leading-5 text-slate-500">{firstRoundReady ? `${workspace.full_name_class_round_one_not_matched.toLocaleString()} records available. Rerunning replaces pass 2 results.` : 'Run pass 1 first.'}</p>
          <details className="mt-2 text-xs text-slate-600"><summary className="text-xs">How class numbers are compared</summary><p className="mt-1 leading-5">The dump uses fullname and user_edu_class. Class numbers are compared directly, without adding 1.</p></details>
        </section>
      </div>
    </Card>
  </>;
}
