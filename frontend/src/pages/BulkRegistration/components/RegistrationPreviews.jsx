export function RegistrationPreviews({ file, output, busy, onOutputPage, usernameVerification, onVerifyUsernames }) {
  return <>
    {output && <>
      <section className="bulk-card bulk-output-summary" aria-labelledby="output-summary-title">
        <div><p className="bulk-card-eyebrow">Generated output</p><h2 id="output-summary-title">{output.sheet || 'Registration records'}</h2><p>{output.row_count} rows prepared across 24 columns.</p></div>
        <div className="bulk-preview-actions"><span className="bulk-badge"><span aria-hidden="true">&#10003;</span> Ready to export</span><button className="bulk-button bulk-verify-button" disabled={busy} onClick={onVerifyUsernames}>Verify usernames</button></div>
      </section>

      {usernameVerification && <UsernameVerification verification={usernameVerification} />}

      {!!output.blank_first_name_records?.length && <section className="bulk-card bulk-quality-card is-error" aria-labelledby="missing-first-names-title">
        <QualityHeading icon="!" eyebrow="Action required" title="Records with blank first names" count={output.blank_first_name_records.length} id="missing-first-names-title" />
        <p className="bulk-quality-description">Add a first name to the source file, then generate the preview again. A first name is required to generate a username.</p>
        <div className="bulk-exception-table-scroll" tabIndex={0} role="region" aria-label="Records with blank first names"><table><thead><tr><th scope="col">Record</th><th scope="col">Admission number</th><th scope="col">Last name</th><th scope="col">Full name</th><th scope="col">Status</th></tr></thead><tbody>{output.blank_first_name_records.map(record => <tr key={`${record.record}-${record.admission_number}`}><td>{record.record}</td><td>{record.admission_number || '\u2014'}</td><td>{record.last_name || '\u2014'}</td><td>{record.full_name || '\u2014'}</td><td><span className="bulk-status-pill is-failed">Needs first name</span></td></tr>)}</tbody></table></div>
      </section>}

      {!!output.missing_sections?.length && <section className="bulk-card bulk-quality-card is-warning" aria-labelledby="missing-sections-title">
        <QualityHeading icon="!" eyebrow="Database update needed" title="Sections not found" count={output.missing_sections.length} id="missing-sections-title" />
        <p className="bulk-quality-description">Insert these values into <code>users_sections</code>, then generate the preview again.</p>
        <div className="bulk-exception-table-scroll" tabIndex={0} role="region" aria-label="Sections not found in the database"><table><thead><tr><th scope="col">Missing section</th><th scope="col">Status</th></tr></thead><tbody>{output.missing_sections.map(section => <tr key={section}><td>{section}</td><td><span className="bulk-status-pill is-warning">Insert required</span></td></tr>)}</tbody></table></div>
      </section>}

      <section className="bulk-card bulk-preview-records" aria-label="Output preview">
        <div className="bulk-preview-title"><div><p className="bulk-card-eyebrow">Data preview</p><h2>Preview records</h2></div><span className="bulk-page-count">Page {output.page || 1} of {output.total_pages || 1}</span></div>
        <p role="status" className="bulk-hint">Showing {output.rows.length} of {output.row_count} generated records.</p>
        {output.sheet !== undefined && output.sheet !== (file?.sheet ?? null) && <p className="bulk-context-note">Showing results from {output.sheet || 'the previous input'}. Generate preview to replace them with the selected worksheet. Downloads use the displayed results' worksheet.</p>}
        <PreviewTable data={output} />
        {(output.total_pages || 1) > 1 && <nav className="bulk-pagination" aria-label="Output preview pages"><button className="bulk-button bulk-secondary" disabled={busy || output.page <= 1} onClick={() => onOutputPage(output.page - 1)}>Previous</button><span>Rows {(output.page - 1) * output.page_size + 1}&ndash;{Math.min(output.page * output.page_size, output.row_count)} of {output.row_count}</span><button className="bulk-button bulk-secondary" disabled={busy || output.page >= output.total_pages} onClick={() => onOutputPage(output.page + 1)}>Next</button></nav>}
      </section>
    </>}

    {file && <details className="bulk-card bulk-input-preview"><summary>Input preview <span>{file.name}</span></summary><p className="bulk-hint">First {file.rows.length} rows of your source file.</p><PreviewTable data={file} /></details>}
  </>;
}

function UsernameVerification({ verification }) {
  return <section className={`bulk-card bulk-username-verification ${verification.passed ? 'is-passed' : 'is-failed'}`} aria-labelledby="username-verification-title">
    <div className="bulk-verification-heading"><div><p className="bulk-card-eyebrow">Three-stage validation</p><h2 id="username-verification-title">Username verification</h2><p>{verification.checked_usernames} generated usernames checked against the preview and database.</p></div><span className={`bulk-verification-result ${verification.passed ? 'is-passed' : 'is-failed'}`}><span aria-hidden="true">{verification.passed ? '\u2713' : '!'}</span> {verification.passed ? 'All checks passed' : 'Review required'}</span></div>
    <div className="bulk-verification-stages">{verification.stages.map((stage, index) => <article className={`bulk-verification-stage ${stage.passed ? 'is-passed' : 'is-failed'}`} key={stage.id}><div className="bulk-stage-number">{String(index + 1).padStart(2, '0')}</div><div className="bulk-stage-copy"><h3>{stage.title}</h3><p>{stage.passed ? 'No issues found' : formatVerificationIssues(stage)}</p></div><span className={`bulk-status-pill ${stage.passed ? 'is-passed' : 'is-failed'}`}>{stage.passed ? 'Passed' : 'Failed'}</span></article>)}</div>
  </section>;
}

function QualityHeading({ icon, eyebrow, title, count, id }) {
  return <div className="bulk-quality-heading"><span className="bulk-quality-icon" aria-hidden="true">{icon}</span><div><p className="bulk-card-eyebrow">{eyebrow}</p><h2 id={id}>{title}</h2></div><span className="bulk-count-badge">{count}</span></div>;
}

function formatVerificationIssues(stage) {
  if (stage.id === 'first_name_match') return stage.issues.map(issue => `${issue.username} does not match ${issue.first_name || 'blank first name'}`).join(', ');
  return stage.issues.join(', ');
}

function PreviewTable({ data }) {
  return <div className="bulk-table-scroll" tabIndex={0} role="region" aria-label="Scrollable file data"><table><thead><tr>{data.columns.map((column, i) => <th scope="col" key={i}>{column}</th>)}</tr></thead><tbody>{data.rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>)}</tbody></table></div>;
}
