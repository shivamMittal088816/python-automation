export function WorkspaceMembers({ members, loading, error }) {
  return <section aria-label="People with access" className="workspace-selector-members">
        <h3>People with access</h3>
        <div aria-live="polite">
          {loading ? <p className="workspace-selector-member-message">Loading members…</p> : error ? null :
            members.length === 0 ? <p className="workspace-selector-member-message">Accepted invitees will appear here.</p> :
            members.map(member => <div key={member.id} className="workspace-selector-member">
              <span className="workspace-selector-avatar" aria-hidden="true">{member.display_name.slice(0, 1).toUpperCase()}</span>
              <div className="workspace-selector-member-copy">
                <strong>{member.display_name}</strong>
                {member.email && <span>{member.email}</span>}
                <span>{member.workflow === 'mapping' ? 'Mapping' : 'Bulk registration'} · {member.role === 'viewer' ? 'View only' : 'Can edit'}</span>
                {member.status !== 'active' && <span className="workspace-selector-member-status">{member.status === 'revoked' ? 'Access revoked' : 'Access expired'}</span>}
              </div>
              <div className="workspace-selector-member-controls">
                <span className={`workspace-selector-role role-${member.role}`}>{member.role === 'viewer' ? 'Viewer' : 'Editor'}</span>
                <button type="button" disabled title="Editing access is coming soon" aria-label={`Edit access for ${member.display_name}`}>Edit access</button>
              </div>
            </div>)}
        </div>
      </section>;
}
