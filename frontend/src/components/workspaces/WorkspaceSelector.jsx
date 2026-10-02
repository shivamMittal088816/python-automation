import { useEffect, useRef, useState } from 'react';
import { JoinWorkflowDialog } from '../invitations/JoinWorkflowDialog';
import { Icon } from '../common/Presentation';
import { useWorkspaceSelector } from './hooks/useWorkspaceSelector';
import { WorkspaceRow } from './WorkspaceRow';
import { WorkspaceMembers } from './WorkspaceMembers';
import { WorkspaceNameDialog } from './WorkspaceNameDialog';
import { WorkspaceDeleteDialog } from './WorkspaceDeleteDialog';
import './workspace-selector.css';

export function WorkspaceSelector({ role = 'owner', workflow = 'mapping', recovery = false }) {
  const dropdown = useRef(null);
  const [open, setOpen] = useState(false);
  const [joinOpen, setJoinOpen] = useState(false);
  const [naming, setNaming] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const { shared, members, loading, error, spaces, switching, setRetry, changeWorkspace, applyName } = useWorkspaceSelector({ open, role, workflow });
  const selected = spaces?.workspaces.find(item => item.id === spaces.active_workspace_id);
  const acceptingInvite = new URLSearchParams(window.location.search).has('invite');
  const nameDialog = naming || (selected?.owned && selected.needs_name && !acceptingInvite ? { mode: 'setup', workspace: selected } : null);
  const currentName = shared ? `Shared ${workflow === 'mapping' ? 'mapping' : 'registration'} workspace` : 'My workspace';

  useEffect(() => {
    const closeOutside = event => {
      if (!dropdown.current?.contains(event.target)) dropdown.current?.removeAttribute('open');
    };
    document.addEventListener('pointerdown', closeOutside);
    return () => document.removeEventListener('pointerdown', closeOutside);
  }, []);

  function closeOnEscape(event) {
    if (event.key === 'Escape' && dropdown.current?.open) {
      event.stopPropagation();
      dropdown.current.removeAttribute('open');
      dropdown.current.querySelector('summary')?.focus();
    }
  }

  function openNameDialog(mode, workspace) {
    dropdown.current?.removeAttribute('open');
    setNaming({ mode, workspace });
  }
  function savedName(result) {
    if (nameDialog.mode === 'create') {
      window.location.assign(workflow === 'mapping' ? '/admission_file_page' : '/bulk-reg');
      return;
    }
    applyName(result);
    setNaming(null);
  }
  function deletedWorkspace(result) {
    if (result.id === spaces?.active_workspace_id) {
      window.location.assign(workflow === 'mapping' ? '/admission_file_page' : '/bulk-reg');
      return;
    }
    setDeleting(null);
    setRetry(value => value + 1);
  }
  const row = item => <WorkspaceRow key={item.id} item={item} current={item.id === spaces?.active_workspace_id} switching={switching} onSelect={changeWorkspace} onRename={item => openNameDialog('rename', item)} onDelete={item => { dropdown.current?.removeAttribute('open'); setDeleting(item); }} />;

  return <><details ref={dropdown} className={`workspace-selector${recovery ? ' workspace-selector-recovery' : ''}`} onKeyDown={closeOnEscape} onToggle={event => setOpen(event.currentTarget.open)}>
    <summary aria-label={recovery ? 'Select workspace' : 'Workspace selector'}>
      <span className={`workspace-selector-trigger-icon${shared ? ' is-shared' : ''}`}><Icon name={shared ? 'link' : 'grid'} className="size-3.5" /></span>
      <span className="workspace-selector-trigger-copy"><strong>{recovery ? 'Select workspace' : spaces?.workspaces.find(item => item.id === spaces.active_workspace_id)?.name || (shared ? `Shared ${workflow === 'mapping' ? 'mapping' : 'registration'}` : currentName)}</strong></span>
      <svg className="workspace-selector-chevron" aria-hidden="true" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="m4 6 4 4 4-4" /></svg>
    </summary>
    <div className="workspace-selector-panel">
      <div className="workspace-selector-panel-header"><strong>Switch workspace</strong><span>Choose a space to work in</span></div>
      {error && <p className="workspace-selector-member-message" role="alert">{error} <button type="button" onClick={() => setRetry(value => value + 1)}>Retry</button></p>}
      <div className="workspace-selector-list">
      <section aria-label="My workspaces"><h3>My workspaces</h3>{spaces ? spaces.workspaces.filter(item => item.owned).map(row) : <p className="workspace-selector-member-message">Loading workspaces…</p>}
        {spaces && !spaces.workspaces.some(item => item.owned) && <p className="workspace-selector-member-message">Create your own workspace below.</p>}
      </section>
      {(!recovery || spaces?.workspaces.some(item => !item.owned)) && <section aria-label="Shared with me"><h3>Shared with me</h3>
        {spaces?.workspaces.some(item => !item.owned) ? spaces.workspaces.filter(item => !item.owned).map(row) : <div className="workspace-selector-empty"><p>No shared workspaces yet</p></div>}
      </section>}
      {!shared && <WorkspaceMembers members={members} loading={loading} error={error} />}
      </div>
      <div className="workspace-selector-actions">
        <button type="button" disabled={switching} onClick={() => openNameDialog('create')}><span className="workspace-selector-action-icon" aria-hidden="true">+</span>Create workspace</button>
        <button type="button" disabled={switching} onClick={() => { dropdown.current?.removeAttribute('open'); setJoinOpen(true); }}><span className="workspace-selector-action-icon"><Icon name="link" className="size-4" /></span>Join with invitation code</button>
      </div>
      <p className="workspace-selector-note" aria-live="polite">{switching ? 'Opening workspace…' : 'Your files stay in their own workspace.'}</p>
    </div>
  </details>{joinOpen && <JoinWorkflowDialog onClose={() => setJoinOpen(false)} />}
    {nameDialog && !joinOpen && !deleting && <WorkspaceNameDialog key={`${nameDialog.mode}-${nameDialog.workspace?.id || 'new'}`} {...nameDialog} workflow={workflow} onClose={() => setNaming(null)} onSaved={savedName} returnFocusRef={dropdown} />}
    {deleting && <WorkspaceDeleteDialog workspace={deleting} onClose={() => setDeleting(null)} onDeleted={deletedWorkspace} returnFocusRef={dropdown} />}</>;
}
