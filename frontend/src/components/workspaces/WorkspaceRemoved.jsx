import { AccountMenu } from '../auth/AccountMenu';
import { WorkspaceSelector } from './WorkspaceSelector';
import './workspace-removed.css';

export function WorkspaceRemoved({ workflow = 'mapping' }) {
  return <main className="workspace-removed-page">
    <div className="workspace-removed-topbar"><span>Student Mapping</span><AccountMenu /></div>
    <section className="workspace-removed-card" aria-labelledby="workspace-removed-title">
      <div role="status" className="workspace-removed-message">
        <span className="workspace-removed-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><rect x="4" y="4" width="16" height="16" rx="4" /><path d="M8 12h8" /></svg></span>
        <div><h1 id="workspace-removed-title">Workspace removed</h1>
        <p>The owner deleted this workspace. Select another workspace to continue.</p></div>
      </div>
      <WorkspaceSelector role="viewer" workflow={workflow} recovery />
      <p className="workspace-removed-hint">Choose an existing workspace or create a new one.</p>
    </section>
  </main>;
}
