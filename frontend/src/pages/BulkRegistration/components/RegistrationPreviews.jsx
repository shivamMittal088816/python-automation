import { useEffect, useState } from 'react';
import { DataTable } from '../../../components/tables/DataTable';

export function RegistrationPreviews({ file, output, busy, onOutputPage, onInputPage, usernameVerification, onVerifyUsernames, emailVerification, onVerifyEmails }) {
  const inputPage = file?.page || 1;
  const inputPageSize = file?.page_size || 20;
  const inputTotalPages = file?.total_pages || Math.max(1, Math.ceil((file?.row_count || 0) / inputPageSize));

  return <>
    {output && <>
      <section className="bulk-card bulk-output-summary" aria-labelledby="output-summary-title">
        <div><p className="bulk-card-eyebrow">Generated output</p><h2 id="output-summary-title">{output.sheet || 'Registration records'}</h2><p>{output.row_count} rows prepared across 24 columns.</p></div>
        <div className="bulk-preview-actions"><span className="bulk-badge"><span aria-hidden="true">&#10003;</span> Ready to export</span><button className="bulk-button bulk-verify-button" disabled={busy} onClick={onVerifyUsernames}>Verify usernames</button><button className="bulk-button bulk-verify-button" disabled={busy} onClick={onVerifyEmails}>Verify emails</button></div>
      </section>

      {usernameVerification && <UsernameVerification verification={usernameVerification} />}
      {emailVerification && <UsernameVerification verification={emailVerification} kind="email" />}

      {!!output.blank_first_name_records?.length && <section className="bulk-card bulk-quality-card is-error" aria-labelledby="missing-first-names-title">
        <QualityHeading icon="!" eyebrow="Action required" title="Records with blank first names" count={output.blank_first_name_records.length} id="missing-first-names-title" />
        <div className="bulk-name-warning">
          <span className="bulk-name-warning-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m10.3 3.9-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3.1l-8-14a2 2 0 0 0-3.4 0Z" /><path d="M12 9v4m0 4h.01" /></svg>
          </span>
          <div className="bulk-name-warning-copy">
            <h3>First name required to generate a username</h3>
            <p>Students listed below cannot receive a username until their first name is provided.</p>
          </div>
        </div>
        <div className="bulk-exception-table-scroll" tabIndex={0} role="region" aria-label="Records with blank first names"><table><thead><tr><th scope="col">Row</th><th scope="col">Admission number</th><th scope="col">Last name</th><th scope="col">Full name</th><th scope="col">Status</th></tr></thead><tbody>{output.blank_first_name_records.map(record => <tr key={`${record.row_number}-${record.admission_number}`}><td>{record.row_number}</td><td>{record.admission_number || '\u2014'}</td><td>{record.last_name || '\u2014'}</td><td>{record.full_name || '\u2014'}</td><td><span className="bulk-status-pill is-failed">Needs first name</span></td></tr>)}</tbody></table></div>
      </section>}

      {!!output.blank_full_name_records?.length && <section className="bulk-card bulk-quality-card is-error" aria-labelledby="missing-full-names-title">
        <QualityHeading icon="!" eyebrow="Action required" title="Records with blank full names" count={output.blank_full_name_records.length} id="missing-full-names-title" />
        <p className="bulk-quality-description">Add a full name to the source file, then generate the preview again.</p>
        <div className="bulk-exception-table-scroll" tabIndex={0} role="region" aria-label="Records with blank full names"><table><thead><tr><th scope="col">Row</th><th scope="col">Admission number</th><th scope="col">First name</th><th scope="col">Last name</th><th scope="col">Status</th></tr></thead><tbody>{output.blank_full_name_records.map(record => <tr key={`${record.row_number}-${record.admission_number}`}><td>{record.row_number}</td><td>{record.admission_number || '\u2014'}</td><td>{record.first_name || '\u2014'}</td><td>{record.last_name || '\u2014'}</td><td><span className="bulk-status-pill is-failed">{record.status}</span></td></tr>)}</tbody></table></div>
      </section>}

      {!!output.missing_sections?.length && <section className="bulk-card bulk-quality-card is-warning" aria-labelledby="missing-sections-title">
        <QualityHeading icon="!" eyebrow="Database update needed" title="Sections not found" count={output.missing_sections.length} id="missing-sections-title" />
        <p className="bulk-quality-description">Fill in blank sections in the source file. Add unknown sections to <code>users_sections</code>, then generate the preview again.</p>
        <div className="bulk-exception-table-scroll" tabIndex={0} role="region" aria-label="Sections not found in the database"><table><thead><tr><th scope="col">Row</th><th scope="col">Student full name</th><th scope="col">Missing section</th><th scope="col">Status</th></tr></thead><tbody>{output.missing_sections.map(record => <tr key={`${record.row_number}-${record.section}`}><td>{record.row_number}</td><td>{record.full_name || '\u2014'}</td><td>{record.section || 'Blank'}</td><td><span className="bulk-status-pill is-warning">{record.section ? 'Insert required' : 'Section is blank'}</span></td></tr>)}</tbody></table></div>
      </section>}

      {!!output.missing_classes?.length && <section className="bulk-card bulk-quality-card is-warning" aria-labelledby="missing-classes-title">
        <QualityHeading icon="!" eyebrow="Class mapping needed" title="Classes not found" count={output.missing_classes.length} id="missing-classes-title" />
        <p className="bulk-quality-description">These classes are blank or not in the built-in class mapping. Correct the class names in the source file, then generate the preview again.</p>
        <div className="bulk-exception-table-scroll" tabIndex={0} role="region" aria-label="Classes not found in the built-in mapping"><table><thead><tr><th scope="col">Row</th><th scope="col">Admission number</th><th scope="col">Student full name</th><th scope="col">Missing class</th><th scope="col">Status</th></tr></thead><tbody>{output.missing_classes.map(record => <tr key={`${record.row_number}-${record.class_name}`}><td>{record.row_number}</td><td>{record.admission_number || '\u2014'}</td><td>{record.full_name || '\u2014'}</td><td>{record.class_name || 'Blank'}</td><td><span className="bulk-status-pill is-warning">{record.status}</span></td></tr>)}</tbody></table></div>
      </section>}

      {!!output.missing_genders?.length && <section className="bulk-card bulk-quality-card is-warning" aria-labelledby="missing-genders-title">
        <QualityHeading icon="!" eyebrow="Gender mapping needed" title="Genders not found" count={output.missing_genders.length} id="missing-genders-title" />
        <p className="bulk-quality-description">These genders are blank or not in the predefined mapping (Male, Female, Others). Correct the gender values in the source file, then generate the preview again.</p>
        <div className="bulk-exception-table-scroll" tabIndex={0} role="region" aria-label="Genders not found in the predefined mapping"><table><thead><tr><th scope="col">Row</th><th scope="col">Admission number</th><th scope="col">Student full name</th><th scope="col">Unmapped gender</th><th scope="col">Status</th></tr></thead><tbody>{output.missing_genders.map(record => <tr key={`${record.row_number}-${record.gender}`}><td>{record.row_number}</td><td>{record.admission_number || '\u2014'}</td><td>{record.full_name || '\u2014'}</td><td>{record.gender || 'Blank'}</td><td><span className="bulk-status-pill is-warning">{record.status}</span></td></tr>)}</tbody></table></div>
      </section>}

      <details open className="bulk-card bulk-preview-records" role="region" aria-label="Output preview">
        <summary className="bulk-preview-title"><div><p className="bulk-card-eyebrow">Data preview</p><h2>Preview records</h2></div><div className="bulk-preview-title-controls"><span className="bulk-page-count">Page {output.page || 1} of {output.total_pages || 1}</span><span className="bulk-collapse-chevron" aria-hidden="true">&#8964;</span></div></summary>
        <p role="status" className="bulk-hint">Showing {output.rows.length} of {output.row_count} generated records.</p>
        {output.sheet !== undefined && output.sheet !== (file?.sheet ?? null) && <p className="bulk-context-note">Showing results from {output.sheet || 'the previous input'}. Generate preview to replace them with the selected worksheet. Downloads use the displayed results' worksheet.</p>}
        <DataTable variant="preview" rows={output.rows} columns={output.columns} ariaLabel="Generated registration records" />
        {(output.total_pages || 1) > 1 && <nav className="bulk-pagination" aria-label="Output preview pages"><span>Rows {(output.page - 1) * output.page_size + 1}&ndash;{Math.min(output.page * output.page_size, output.row_count)} of {output.row_count}</span><div className="bulk-pagination-controls"><button className="bulk-button bulk-secondary" disabled={busy || output.page <= 1} onClick={() => onOutputPage(output.page - 1)}>Previous</button><PageJump idPrefix="output" page={output.page} totalPages={output.total_pages} busy={busy} onGo={onOutputPage} /><button className="bulk-button bulk-secondary" disabled={busy || output.page >= output.total_pages} onClick={() => onOutputPage(output.page + 1)}>Next</button></div></nav>}
      </details>
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

function UsernameVerification({ verification, kind = 'username' }) {
  const email = kind === 'email';
  return <details open className={`bulk-card bulk-username-verification ${verification.passed ? 'is-passed' : 'is-failed'}`}>
    <summary className="bulk-verification-heading">
      <div><p className="bulk-card-eyebrow">{verification.stages.length}-stage validation</p><h2>{email ? 'Email verification' : 'Username verification'}</h2><p>{email ? verification.checked_emails : verification.checked_usernames} student records checked for blank values and against the preview and database.</p></div>
      <div className="bulk-verification-controls"><span className={`bulk-verification-result ${verification.passed ? 'is-passed' : 'is-failed'}`}><span aria-hidden="true">{verification.passed ? '\u2713' : '!'}</span> {verification.passed ? 'All checks passed' : 'Review required'}</span><span className="bulk-collapse-chevron" aria-hidden="true">&#8964;</span></div>
    </summary>
    <div className="bulk-verification-stages">{verification.stages.map((stage, index) => <article className={`bulk-verification-stage ${stage.passed ? 'is-passed' : 'is-failed'}`} key={stage.id}>
      <div className="bulk-stage-number">{String(index + 1).padStart(2, '0')}</div>
      <div className="bulk-stage-copy"><h3>{stage.title}</h3><p>{stage.passed ? 'No issues found' : formatVerificationIssues(stage)}</p></div>
      <span className={`bulk-status-pill ${stage.passed ? 'is-passed' : 'is-failed'}`}>{stage.passed ? 'Passed' : 'Failed'}</span>
      {!stage.passed && stage.failed_records?.row_count > 0 && <details className="bulk-failed-records">
        <summary>Preview students who failed ({stage.failed_records.row_count})</summary>
        <p className="bulk-hint">Complete student records for this check. Preview row refers to the full generated output.</p>
        <DataTable variant="preview" rows={stage.failed_records.rows} columns={stage.failed_records.columns} ariaLabel="Students who failed verification" />
      </details>}
    </article>)}</div>
  </details>;
}

function QualityHeading({ icon, eyebrow, title, count, id }) {
  return <div className="bulk-quality-heading"><span className="bulk-quality-icon" aria-hidden="true">{icon}</span><div><p className="bulk-card-eyebrow">{eyebrow}</p><h2 id={id}>{title}</h2></div><span className="bulk-count-badge">{count}</span></div>;
}

function formatVerificationIssues(stage) {
  if (stage.id === 'blank_values') return `${stage.issues.length} student records have a blank value. Preview the students below.`;
  if (stage.id === 'first_name_match') return stage.issues.map(issue => `${issue.username} does not match ${issue.first_name || 'blank first name'}`).join(', ');
  return stage.issues.join(', ');
}

