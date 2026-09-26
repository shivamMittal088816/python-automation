export function RegistrationPreviews({ file, output }) {
  return (
    <>
      {output && <section className="bulk-card bulk-preview" aria-label="Output preview">
        <div className="bulk-preview-title">
          <h2>Output preview{output.sheet ? ` / ${output.sheet}` : ''}</h2>
          <span className="bulk-badge">Ready to export</span>
        </div>
        <p role="status" className="bulk-hint">{output.row_count} rows &middot; 24 columns &middot; Showing first {output.rows.length} rows</p>{output.sheet !== undefined && output.sheet !== (file?.sheet ?? null) && <p className="bulk-hint">Showing results from {output.sheet || 'the previous input'}. Generate preview to replace them with the selected worksheet. Downloads use the displayed results' worksheet.</p>}<PreviewTable data={output} />
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
