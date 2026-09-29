import { useEffect, useState } from 'react';
import { DataTable } from '../../../components/tables/DataTable';

export function RegistrationPreviews({ file, output, busy, onOutputPage, onInputPage, outputVerification, usernameChanges, onVerifyOutput }) {
  const inputPage = file?.page || 1;
  const inputPageSize = file?.page_size || 20;
  const inputTotalPages = file?.total_pages || Math.max(1, Math.ceil((file?.row_count || 0) / inputPageSize));

  return <>
    {output && <>
      <section className="bulk-card bulk-output-summary" aria-labelledby="output-summary-title">
        <div><p className="bulk-card-eyebrow">Generated output</p><h2 id="output-summary-title">{output.sheet || 'Registration records'}</h2><p>{output.row_count} rows prepared across 24 columns.</p></div>
        <div className="bulk-preview-actions"><span className="bulk-badge"><span aria-hidden="true">&#10003;</span> Ready to export</span></div>
      </section>

      {!!output.review_records?.length && <details open className="bulk-card bulk-quality-card is-error" aria-labelledby="preview-review-title">
        <summary className="bulk-preview-title"><QualityHeading icon="!" eyebrow="Action required" title="Review records" count={output.review_records.length} id="preview-review-title" /><span className="bulk-collapse-chevron" aria-hidden="true">&#8964;</span></summary>
        <p className="bulk-quality-description">All issues found while generating the preview are grouped by student below. Correct the source file, then generate the preview again.</p>
        <div className="bulk-exception-table-scroll" tabIndex={0} role="region" aria-label="Records requiring review"><table><thead><tr><th scope="col">Row</th><th scope="col">Admission number</th><th scope="col">Student full name</th><th scope="col">Issues</th></tr></thead><tbody>{output.review_records.map(record => <tr key={record.row_number}><td>{record.row_number}</td><td>{record.admission_number || '\u2014'}</td><td>{record.full_name || '\u2014'}</td><td><div className="bulk-sanity-problems">{record.issues.map(issue => <span key={issue} className="bulk-status-pill is-failed">{issue}</span>)}</div></td></tr>)}</tbody></table></div>
      </details>}

      <details open className="bulk-card bulk-preview-records" role="region" aria-label="Output preview">
        <summary className="bulk-preview-title"><div><p className="bulk-card-eyebrow">Data preview</p><h2>Preview records</h2></div><div className="bulk-preview-title-controls"><span className="bulk-page-count">Page {output.page || 1} of {output.total_pages || 1}</span><span className="bulk-collapse-chevron" aria-hidden="true">&#8964;</span></div></summary>
        <p role="status" className="bulk-hint">Showing {output.rows.length} of {output.row_count} generated records.</p>
        {output.sheet !== undefined && output.sheet !== (file?.sheet ?? null) && <p className="bulk-context-note">Showing results from {output.sheet || 'the previous input'}. Generate preview to replace them with the selected worksheet. Downloads use the displayed results' worksheet.</p>}
        <DataTable variant="preview" rows={output.rows} columns={output.columns} ariaLabel="Generated registration records" />
        {(output.total_pages || 1) > 1 && <nav className="bulk-pagination" aria-label="Output preview pages"><span>Rows {(output.page - 1) * output.page_size + 1}&ndash;{Math.min(output.page * output.page_size, output.row_count)} of {output.row_count}</span><div className="bulk-pagination-controls"><button className="bulk-button bulk-secondary" disabled={busy || output.page <= 1} onClick={() => onOutputPage(output.page - 1)}>Previous</button><PageJump idPrefix="output" page={output.page} totalPages={output.total_pages} busy={busy} onGo={onOutputPage} /><button className="bulk-button bulk-secondary" disabled={busy || output.page >= output.total_pages} onClick={() => onOutputPage(output.page + 1)}>Next</button></div></nav>}
      </details>

      <section className="bulk-card bulk-output-summary" aria-labelledby="bulk-reg-verify-title">
        <div><p className="bulk-card-eyebrow">Final file validation</p><h2 id="bulk-reg-verify-title">Bulk-reg verify</h2><p>Check all final-file sanity rules, account uniqueness, database conflicts, and username-to-first-name matching.</p></div>
        <button className="bulk-button bulk-verify-button" disabled={busy} onClick={onVerifyOutput}>Bulk-reg verify</button>
      </section>
      {!!usernameChanges?.length && <section className="bulk-card bulk-quality-card is-warning" aria-labelledby="username-changes-title">
        <QualityHeading icon="↻" eyebrow="Automatically corrected" title="Regenerated usernames" count={usernameChanges.length} id="username-changes-title" />
        <p className="bulk-quality-description">Conflicting usernames were regenerated and saved to the final file. Emails generated from blank input values were updated to match; supplied emails were preserved.</p>
        <div className="bulk-exception-table-scroll" tabIndex={0} role="region" aria-label="Regenerated usernames"><table><thead><tr><th scope="col">Row</th><th scope="col">Admission number</th><th scope="col">First name</th><th scope="col">Previous username</th><th scope="col">New username</th><th scope="col">Result</th></tr></thead><tbody>{usernameChanges.map(change => <tr key={`${change.row_number}-${change.new_username}`}><td>{change.row_number}</td><td>{change.admission_number || '\u2014'}</td><td>{change.first_name || '\u2014'}</td><td>{change.previous_username || 'Blank'}</td><td>{change.new_username}</td><td>{change.message}</td></tr>)}</tbody></table></div>
      </section>}
      {outputVerification && <BulkRegistrationVerification verification={outputVerification} />}
    </>}

    {file && <details className="bulk-card bulk-input-preview"><summary>Input preview <span>{file.name}</span></summary><p className="bulk-hint">Showing {file.rows.length} of {file.row_count} source records.</p><DataTable variant="preview" rows={file.rows} columns={file.columns} ariaLabel="Input registration records" />{inputTotalPages > 1 && <nav className="bulk-pagination" aria-label="Input preview pages"><span>Rows {(inputPage - 1) * inputPageSize + 1}&ndash;{Math.min(inputPage * inputPageSize, file.row_count)} of {file.row_count}</span><div className="bulk-pagination-controls"><button className="bulk-button bulk-secondary" disabled={busy || inputPage <= 1} onClick={() => onInputPage(inputPage - 1)}>Previous</button><PageJump idPrefix="input" page={inputPage} totalPages={inputTotalPages} busy={busy} onGo={onInputPage} /><button className="bulk-button bulk-secondary" disabled={busy || inputPage >= inputTotalPages} onClick={() => onInputPage(inputPage + 1)}>Next</button></div></nav>}</details>}
  </>;
}

function PageJump({ idPrefix, page, totalPages, busy, onGo }) {
  const [value, setValue] = useState(String(page));
  useEffect(() => setValue(String(page)), [page]);

  function submit(event) {
    event.preventDefault();
    const requested = Number(value);
    if (Number.isInteger(requested) && requested >= 1 && requested <= totalPages && requested !== page) {
      onGo(requested);
    }
  }

  const requested = Number(value);
  const valid = Number.isInteger(requested) && requested >= 1 && requested <= totalPages;
  const inputId = `bulk-${idPrefix}-preview-page`;
  const totalId = `${inputId}-total`;
  return <form className="bulk-page-jump" onSubmit={submit}>
    <label htmlFor={inputId}>Page</label>
    <input id={inputId} type="number" min="1" max={totalPages} step="1" value={value} disabled={busy} onChange={event => setValue(event.target.value)} aria-describedby={totalId} />
    <span id={totalId}>of {totalPages}</span>
    <button className="bulk-button bulk-secondary" type="submit" disabled={busy || !valid || requested === page}>Go</button>
  </form>;
}

function BulkRegistrationVerification({ verification }) {
  const failedStages = verification.stages.filter(stage => !stage.passed);
  return <details open className={`bulk-card bulk-username-verification ${verification.passed ? 'is-passed' : 'is-failed'}`}>
    <summary className="bulk-verification-heading">
      <div><p className="bulk-card-eyebrow">{failedStages.length ? `${failedStages.length} failed checks` : 'Final validation'}</p><h2>Bulk-reg verification</h2><p>{verification.checked_records} records checked in the saved generated file.</p></div>
      <div className="bulk-verification-controls"><span className={`bulk-verification-result ${verification.passed ? 'is-passed' : 'is-failed'}`}><span aria-hidden="true">{verification.passed ? '\u2713' : '!'}</span> {verification.passed ? 'All checks passed' : 'Review required'}</span><span className="bulk-collapse-chevron" aria-hidden="true">&#8964;</span></div>
    </summary>
    {!!failedStages.length && <div className="bulk-verification-stages">{failedStages.map((stage, index) => <article className="bulk-verification-stage is-failed" key={stage.id}>
      <div className="bulk-stage-number">{String(index + 1).padStart(2, '0')}</div>
      <div className="bulk-stage-copy"><h3>{stage.title}</h3><p>{formatVerificationIssues(stage)}</p></div>
      <span className="bulk-status-pill is-failed">Failed</span>
      {stage.failed_records?.row_count > 0 && <details className="bulk-failed-records">
        <summary>Preview students who failed ({stage.failed_records.row_count})</summary>
        <p className="bulk-hint">Complete student records for this check. Preview row refers to the full generated output.</p>
        <DataTable variant="preview" rows={stage.failed_records.rows} columns={stage.failed_records.columns} ariaLabel="Students who failed verification" />
      </details>}
    </article>)}</div>}
  </details>;
}

function QualityHeading({ icon, eyebrow, title, count, id }) {
  return <div className="bulk-quality-heading"><span className="bulk-quality-icon" aria-hidden="true">{icon}</span><div><p className="bulk-card-eyebrow">{eyebrow}</p><h2 id={id}>{title}</h2></div><span className="bulk-count-badge">{count}</span></div>;
}

function formatVerificationIssues(stage) {
  if (stage.id.startsWith('blank_')) return `${stage.issues.length} student records have a blank value. Preview the students below.`;
  if (stage.id === 'username_first_name_match') return stage.issues.map(issue => `${issue.username || 'blank username'} does not match ${String(issue.first_name || 'blank first name').toLowerCase()}`).join(', ');
  if (['first_name_required', 'first_name_characters', 'last_name_characters', 'full_name_required', 'full_name_characters', 'section_index', 'class_index', 'gender_index', 'email_format'].includes(stage.id)) return `${stage.issues.length} student ${stage.issues.length === 1 ? 'record fails' : 'records fail'} this check. Preview ${stage.issues.length === 1 ? 'the student' : 'those students'} below.`;
  return stage.issues.join(', ');
}

