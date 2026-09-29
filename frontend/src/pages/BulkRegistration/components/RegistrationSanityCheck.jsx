import { useState } from 'react';

export function RegistrationSanityCheck({ source, busy, result, onCheck }) {
  const [expanded, setExpanded] = useState(true);
  return <section className="bulk-card bulk-sanity" aria-labelledby="sanity-title">
    <div className="bulk-sanity-header">
      <h2 id="sanity-title"><button type="button" className="bulk-sanity-toggle" aria-expanded={expanded} aria-controls="bulk-sanity-content" onClick={() => setExpanded(value => !value)}>
        <span>Input sanity check</span><span className={`bulk-sanity-chevron ${expanded ? 'is-expanded' : ''}`} aria-hidden="true">›</span>
      </button></h2>
      <div className="bulk-actions">
        <button className="bulk-button bulk-secondary" disabled={busy || !source} onClick={() => { setExpanded(true); onCheck(); }}>Sanity check</button>
      </div>
    </div>
    <div id="bulk-sanity-content" hidden={!expanded}>
      {result ? <SanityResults result={result} /> : <p className="bulk-sanity-footnote">Check missing details and duplicate emails.</p>}
    </div>
  </section>;
}

function SanityResults({ result }) {
  const [page, setPage] = useState(1);
  const records = result.rows.filter(row => row.problems.length);
  const pages = Math.max(1, Math.ceil(records.length / 20));
  const currentPage = Math.min(page, pages);
  return <>
    <div className="bulk-sanity-summary" role="status" aria-label={`${result.row_count} records checked · ${result.failed_count} with issues · ${result.row_count - result.failed_count} passed`}>
      <div><strong>{result.row_count}</strong><span>checked</span></div>
      <div className="is-failed"><strong>{result.failed_count}</strong><span>failed</span></div>
      <div className="is-passed"><strong>{result.row_count - result.failed_count}</strong><span>passed</span></div>
    </div>
    <ul className="bulk-sanity-checks">{result.checks.map(check => <li key={check.id}>
      <span className={`bulk-sanity-icon ${check.passed ? 'is-passed' : 'is-failed'}`} aria-hidden="true">{check.passed ? '✓' : '✕'}</span>
      <div><strong>{({ first_name: 'First name', section: 'Section', class: 'Class', full_name: 'Full name', gender: 'Gender', email_format: 'Email format', duplicate_email: 'Unique emails', username: 'Username must be blank' })[check.id] || check.label}</strong><span className={check.passed ? 'is-passed' : 'is-failed'}>{check.passed ? 'Passed' : `${check.failed_count} failed`}</span></div>
    </li>)}</ul>
    <div className="bulk-sanity-records-heading"><h3>Failed students <span>{records.length}</span></h3>{!!records.length && <p>Fix in source file and re-upload.</p>}</div>
    {!!records.length && <div className="bulk-exception-table-scroll" tabIndex={0} role="region" aria-label="Sanity check records">
      <table><thead><tr><th scope="col">Row number</th>{result.columns.map((column, index) => <th scope="col" key={index}>{column}</th>)}<th scope="col">Status</th></tr></thead>
        <tbody>{records.slice((currentPage - 1) * 20, currentPage * 20).map(row => <tr key={row.row_number}>
          <td>{row.row_number}</td>{row.values.map((value, index) => <td key={index}>{value === '' ? '—' : value}</td>)}
          <td><div className="bulk-sanity-problems">{row.problems.map(problem => <span key={problem} className="bulk-status-pill is-failed">{problem}</span>)}</div></td>
        </tr>)}</tbody></table>
    </div>}
    {!records.length && <div className="bulk-sanity-empty"><span aria-hidden="true">✓</span><div><strong>All students passed</strong><p>No records with issues.</p></div></div>}
    {pages > 1 && <nav className="bulk-pagination" aria-label="Sanity check pages">
      <button className="bulk-button bulk-secondary" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>Previous</button>
      <span>Page {currentPage} of {pages}</span>
      <button className="bulk-button bulk-secondary" disabled={currentPage === pages} onClick={() => setPage(currentPage + 1)}>Next</button>
    </nav>}
    <p className="bulk-sanity-footnote">All values are trimmed before checking. First name: A–Z and a–z only; last and full names also allow spaces. Class validation checks the Class Number column.</p>
  </>;
}
