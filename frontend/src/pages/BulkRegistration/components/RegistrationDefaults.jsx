export function RegistrationDefaults() {
  return (
    <aside className="bulk-card bulk-defaults">
      <div className="bulk-defaults-title">
        <span className="bulk-eyebrow">OUTPUT SETTINGS</span>
        <span className="bulk-format">2026</span>
      </div>
      <h2>Predefined output values</h2>
      <p className="bulk-defaults-description">Applied automatically to every row.</p>
      <dl className="bulk-defaults-summary">
        <div><dt>User type</dt><dd>Student</dd></div>
        <div><dt>Package</dt><dd>14</dd></div>
        <div><dt>Year</dt><dd>2026</dd></div>
      </dl>
      <details className="bulk-defaults-details">
        <summary>View all output values</summary>
        <table>
          <caption className="sr-only">Predefined output values</caption>
          <thead>
            <tr>
              <th scope="col">Field</th>
              <th scope="col">Value</th>
            </tr>
          </thead>
          <tbody>{[
            ['Category', '0'], ['User type', 'Student'],
            ['Subscription date', '2026-04-01 00:00:00'], ['Package', '14'],
            ['Activated', '1'], ['Subscribed', '1'], ['Year', '2026'],
          ].map(([label, value]) => <tr key={label}>
              <th scope="row">{label}</th>
              <td>{value}</td>
            </tr>)}</tbody>
        </table>
      </details>
      <div className="bulk-output-note">
        <strong>24 columns. One consistent format.</strong>
        <p>School details and predefined values replace input values. Other supplied values are kept; missing fields stay blank.</p>
      </div>
    </aside>
  );
}
