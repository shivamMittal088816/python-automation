export function SchoolVerification({ schoolIndex, school, schoolValid, busy, verifySchool, edit }) {
  return (
    <section className="bulk-card" aria-labelledby="school-title">
      <div className="bulk-section-title">
        <span className="bulk-step">01</span>
        <div>
          <h2 id="school-title">Verify your school</h2>
          <p>We'll fetch the school name using its index.</p>
        </div>{schoolValid && <span className="bulk-badge">Verified</span>}</div>
      <form onSubmit={verifySchool} className="bulk-inline-form">
        <div className="bulk-field">
          <label htmlFor="bulk-school-index">School index</label>
          <input id="bulk-school-index" required pattern="[0-9]+" inputMode="numeric" placeholder="Enter school index" disabled={busy} value={schoolIndex} onChange={event => { edit({ schoolIndex: event.target.value, school: null, output: null }); }} />
          </div>
          <button disabled={busy || !/^[0-9]+$/.test(schoolIndex.trim())} className="bulk-button bulk-primary">Verify school index</button>
        </form>
        {schoolValid && <div className="bulk-verified">
          <p role="status">School index verified</p>
          <label htmlFor="bulk-school-name">School name fetched</label>
          <input id="bulk-school-name" readOnly value={school.school_name} />
        </div>}
      </section>
  );
}
