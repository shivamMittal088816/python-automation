export function RegistrationPreviews({ file, output, busy, onOutputPage }) {
  return (
    <>
      {output && <section className="bulk-card bulk-preview" aria-label="Output preview">
        <div className="bulk-preview-title">
          <h2>Output preview{output.sheet ? ` / ${output.sheet}` : ''}</h2>
          <span className="bulk-badge">Ready to export</span>
        </div>
        <p role="status" className="bulk-hint">{output.row_count} rows &middot; 24 columns &middot; Page {output.page || 1} of {output.total_pages || 1}</p>{output.sheet !== undefined && output.sheet !== (file?.sheet ?? null) && <p className="bulk-hint">Showing results from {output.sheet || 'the previous input'}. Generate preview to replace them with the selected worksheet. Downloads use the displayed results' worksheet.</p>}<PreviewTable data={output} />
        {!!output.missing_sections?.length && <section className="bulk-missing-sections" aria-labelledby="missing-sections-title">
          <h3 id="missing-sections-title">Sections not found in the database</h3>
          <p>Insert these sections into <code>users_sections</code>, then generate the preview again.</p>
          <table>
            <thead><tr><th scope="col">Missing section</th><th scope="col">Status</th></tr></thead>
            <tbody>{output.missing_sections.map(section => <tr key={section}><td>{section}</td><td>Not found &mdash; insert required</td></tr>)}</tbody>
          </table>
        </section>}
        {(output.total_pages || 1) > 1 && <nav className="bulk-pagination" aria-label="Output preview pages">
          <button className="bulk-button bulk-secondary" disabled={busy || output.page <= 1} onClick={() => onOutputPage(output.page - 1)}>Previous</button>
          <span>Rows {(output.page - 1) * output.page_size + 1}&ndash;{Math.min(output.page * output.page_size, output.row_count)} of {output.row_count}</span>
          <button className="bulk-button bulk-secondary" disabled={busy || output.page >= output.total_pages} onClick={() => onOutputPage(output.page + 1)}>Next</button>
        </nav>}
      </section>}
      {file && <details className="bulk-card bulk-input-preview">
        <summary>Input preview <span>{file.name}</span>
        </summary>
        <p className="bulk-hint">First {file.rows.length} rows of your source file.</p>
        <PreviewTable data={file} />
      </details>}
    </>
  );
}

function PreviewTable({ data }) {
  return <div className="bulk-table-scroll" tabIndex={0} role="region" aria-label="Scrollable file data">
<table>
<thead>
<tr>{data.columns.map((column, i) => <th scope="col" key={i}>{column}</th>)}</tr>
</thead>
<tbody>{data.rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>)}</tbody>
</table>
</div>;
}
