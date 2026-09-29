export function RegistrationActions({ schoolValid, source, busy, output, convert, sanity }) {
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
        <button disabled={busy || !schoolValid || !source} onClick={() => convert()} className="bulk-button bulk-primary">Generate preview</button>{output && ['xlsx', 'csv'].map(format => <button key={format} disabled={busy} onClick={() => convert(format)} className="bulk-button bulk-secondary">Download {format.toUpperCase()}</button>)}</div>
    </section>
  );
}
