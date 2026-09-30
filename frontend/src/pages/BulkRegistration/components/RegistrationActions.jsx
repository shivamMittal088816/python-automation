export function RegistrationActions({ schoolValid, source, busy, output, outputVerified, convert, sanity }) {
  return (
    <section className="bulk-action-bar" aria-label="Generate output">
      <div className="bulk-section-title">
        <span className="bulk-step">03</span>
        <div>
          <h2>Ready to convert</h2>
          <p>{schoolValid && source ? (sanity ? 'Sanity check complete. Review any issues before generating a preview.' : 'Run the input sanity check before generating a preview.') : 'Verify your school and add a file to get started.'}</p>
        </div>
      </div>
      <div className="bulk-actions">
        <button disabled={busy || !schoolValid || !source} onClick={() => convert()} className="bulk-button bulk-primary">Generate preview</button>{output && ['xlsx', 'csv'].map(format => <button key={format} disabled={busy || !outputVerified} title={outputVerified ? `Download verified ${format.toUpperCase()} file` : 'Run Bulk-reg verify successfully to enable downloads'} onClick={() => convert(format)} className="bulk-button bulk-secondary">Download {format.toUpperCase()}</button>)}</div>
      {output && !outputVerified && <p className="bulk-hint">Run Bulk-reg verify successfully before downloading the final file.</p>}
    </section>
  );
}
