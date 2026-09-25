import { useSessionValue } from '../../hooks/useSessionValue';
import { RunColumns } from '../../components/common/RunColumns';
import { useWorkspace } from '../../context/WorkspaceContext';
import { emailMappingApi } from '../../services/emailMappingApi';
import { fileApi } from '../../services/fileApi';
import { Alert, Button, Card, DownloadButton, Select } from '../../components/common/Controls';
import { MappingResultCards } from '../../components/common/MappingResultCards';
import { SectionHeader } from '../../components/common/Presentation';

export function EmailForm({ schoolSource, admissionSource }) {
  const { workspace, id, busy, run, clearNotice } = useWorkspace();
  const [draft, setDraft] = useSessionValue(`${id}:email-draft:${workspace.files.school?.version}:${workspace.settings.admission_school_sheet}`, {});
  const values = { ...workspace.settings, ...draft };
  const inputSource = values.email_input_source || 'school_file';
  const source = inputSource === 'admission_not_matched' ? admissionSource : schoolSource;
  const columns = schoolSource?.columns || [];
  const suggestions = schoolSource?.suggestions || {};
  const normalized = value => String(value).toLowerCase().replace(/[^a-z0-9]/g, '');
  const suggestedEmail = columns.includes(suggestions.email_column)
    ? suggestions.email_column
    : columns.find(column => normalized(column).includes('email'));
  const suggestedFirstName = columns.includes(suggestions.first_name_column)
    ? suggestions.first_name_column
    : columns.find(column => ['firstname', 'first', 'studentfirstname'].includes(normalized(column)));
  const suggestedName = columns.includes(suggestions.full_name_column) ? suggestions.full_name_column : columns[0];
  const savedEmail = values.email_input_column === null ? '' : values.email_input_column;
  const email = savedEmail === '' ? '' : columns.includes(savedEmail) ? savedEmail : suggestedEmail || '';
  const savedFirstName = values.email_first_name_column;
  const firstName = columns.includes(savedFirstName) ? savedFirstName : suggestedFirstName || suggestedName;
  const update = settings => {
    clearNotice();
    setDraft(previous => ({ ...previous, ...settings }));
  };

  return <div className="space-y-4">
    <p className="caption">Choose whether Email mapping processes the complete school file or only students not matched by Admission mapping.</p>
    <Card>
      <SectionHeader title="Email mapping settings" description="Choose the student source, then select email and first-name columns from the school file headers." />
      <fieldset className="mb-4" disabled={!!busy}>
        <legend className="mb-3 text-sm font-semibold">Email mapping input</legend>
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            ['school_file', 'School file', schoolSource],
            ['admission_not_matched', 'Admission mapping — Not matched', admissionSource],
          ].map(([value, label, metadata]) => <label key={value} className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${inputSource === value ? 'border-blue-400 bg-blue-50 text-blue-900' : 'border-slate-200'}`}>
            <input type="radio" name="email-mapping-source" value={value} checked={inputSource === value} onChange={() => update({ email_input_source: value })} />
            <span>{label}<span className="mt-1 block text-xs text-slate-500">{metadata ? `${Number(metadata.total || 0).toLocaleString()} students` : 'Run Admission mapping first'}</span></span>
          </label>)}
        </div>
      </fieldset>
      {inputSource === 'admission_not_matched' && !admissionSource && <Alert type="warning">First run Admission mapping to use its Not matched students.</Alert>}
      {source && <>
        <p className="mb-3 caption">Loaded {Number(source.total || 0).toLocaleString()} students from {inputSource === 'school_file' ? 'the school file' : 'Admission mapping — Not matched'}. A separate SQL dump will be fetched using their emails across all schools.</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <Select label="School email column" value={email} disabled={!!busy} options={[{ value: '', label: 'Choose an email column' }, ...columns]} onChange={event => update({ email_input_column: event.target.value || null })} />
          {email && <Select label="School first name column" value={firstName} disabled={!!busy} options={columns} onChange={event => update({ email_first_name_column: event.target.value })} />}
        </div>
        {!email ? <Alert type="warning">The selected input has no email data selected. Choose its email column.</Alert> :
          <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50/50 p-4">
            <h4 className="text-sm font-semibold text-blue-900">Email and first name <RunColumns stage="email" pass="1" /></h4>
            <p className="my-3 caption">Duplicate school emails go to Review. Otherwise, a unique email and matching first name is Matched. One-character, missing, or different names and duplicate accounts go to Review; emails not found go to Not matched.</p>
            <Button primary disabled={!!busy || !firstName} onClick={() => run('Fetching users by email and mapping students...', () => emailMappingApi.run(id, {
              source: inputSource,
              email_column: email,
              name_column: firstName,
            }))}>Run mapping</Button>
          </div>}
      </>}
      {workspace.files.email_dump && <details className="mt-3"><summary className="text-sm font-medium">E-mail dump file</summary><p className="my-3 caption">Separate email lookup file: email_dump.csv. The admission dump is unchanged.</p><DownloadButton action={() => fileApi.download(id, 'email_dump')}>Download e-mail dump file</DownloadButton></details>}
    </Card>
    {Object.keys(workspace.exports.email).length > 0 && <MappingResultCards stage="email" previewPath="/email_preview_page" title="Mapping results" />}
  </div>;
}
