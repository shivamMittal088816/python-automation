export function RegistrationDefaults() {
  return (
    <aside className="bulk-card bulk-defaults">
      <div className="bulk-defaults-title">
        <span className="bulk-eyebrow">OUTPUT SETTINGS</span>
        <span className="bulk-format">2026</span>
        <button type="button" className="bulk-button bulk-secondary" disabled title="Modify output values — coming soon">Modify</button>
      </div>
      <table>
        <caption>Predefined output values<span>Applied automatically to every row.</span>
        </caption>
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
      <div className="bulk-output-note">
        <strong>24 columns. One consistent format.</strong>
        <p>School details and predefined values replace input values. Other supplied values are kept; missing fields stay blank.</p>
      </div>
    </aside>
  );
}
