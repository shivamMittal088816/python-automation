import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Icon } from '../common/Presentation';
import { createWorkspace, renameWorkspace } from '../../services/workspaces/api';
import './workspace-name.css';

export function WorkspaceNameDialog({ mode, workspace, workflow, onClose, onSaved, returnFocusRef }) {
  const dialog = useRef(null);
  const input = useRef(null);
  const pending = useRef(false);
  const active = useRef(true);
  const titleId = useId(), helpId = useId(), inputId = useId();
  const [name, setName] = useState(mode === 'rename' ? workspace.name : '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const setup = mode === 'setup';
  const trimmed = name.trim();
  const label = workflow === 'mapping' ? 'Student mapping' : 'Bulk registration';

  useEffect(() => {
    const element = dialog.current;
    active.current = true;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    element.showModal();
    input.current?.focus();
    if (mode === 'rename') input.current?.select();
    document.body.style.overflow = 'hidden';
    return () => {
      active.current = false;
      element.close();
      document.body.style.overflow = previousOverflow;
      (returnFocusRef?.current?.querySelector('summary') || previousFocus)?.focus();
    };
  }, [mode, returnFocusRef]);

  async function submit(event) {
    event.preventDefault();
    if (pending.current) return;
    if (!trimmed || trimmed.length > 100 || /[\u0000-\u001f\u007f]/.test(trimmed)) {
      setError('Enter a name of 1–100 characters without control characters.');
      return;
    }
    pending.current = true;
    setSaving(true);
    setError('');
    try {
      const result = mode === 'create'
        ? await createWorkspace(workflow, trimmed)
        : await renameWorkspace(workspace.id, trimmed);
      if (active.current) onSaved(result);
    } catch (err) {
      if (active.current) setError(err.message || 'Could not save the workspace name. Please try again.');
    } finally {
      pending.current = false;
      if (active.current) setSaving(false);
    }
  }

  const close = () => { if (!saving && !setup) onClose(); };
  return createPortal(<dialog ref={dialog} className={`workspace-name-dialog${mode === 'rename' ? ' workspace-name-dialog-dark' : ''}`} aria-labelledby={titleId} aria-describedby={helpId}
    onCancel={event => { event.preventDefault(); close(); }}
    onClick={event => { if (event.target === event.currentTarget) close(); }}>
    <form onSubmit={submit}>
      <header className="workspace-name-header">
        {!setup && <button className="workspace-name-close" type="button" aria-label="Close workspace name dialog" onClick={close} disabled={saving}>×</button>}
        <span className="workspace-name-mark"><Icon name="grid" className={mode === 'rename' ? 'size-4' : 'size-6'} /></span>
        {mode !== 'rename' && <p className="workspace-name-eyebrow">{setup ? 'MAKE IT YOURS' : 'A FRESH START'}</p>}
        <h2 id={titleId}>{setup ? 'A space of your own' : mode === 'create' ? 'Create your workspace' : 'Rename workspace'}</h2>
        <p id={helpId}>{mode === 'rename' ? 'Update how this workspace appears to your team.' : 'Give your workspace a name. A school, a team, or your next project.'}</p>
      </header>
      <div className="workspace-name-body">
        <label htmlFor={inputId}>Workspace name <span>{mode === 'rename' ? `${name.length} / 100` : `${name.length}/100`}</span></label>
        <input ref={input} id={inputId} value={name} onChange={event => { setName(event.target.value); setError(''); }}
          placeholder="e.g. Greenfield School admissions" maxLength={100} autoComplete="off" disabled={saving}
          aria-invalid={Boolean(error)} aria-describedby={helpId} required />
        {error && <p className="workspace-name-error" role="alert">{error}</p>}
        <div className="workspace-name-preview" aria-label="Workspace preview">
          <span className="workspace-name-avatar">{Array.from(trimmed || 'W')[0].toLocaleUpperCase()}</span>
          <div><strong>{trimmed || 'Your workspace name'}</strong><span>{mode === 'rename' ? (workflow === 'mapping' ? 'Student Mapping' : 'Bulk registration') : <>{label} <span aria-hidden="true">·</span> You’re the owner</>}</span></div>
          <span className="workspace-name-preview-badge">{mode === 'rename' ? 'Owner' : 'Your space'}</span>
        </div>
        <p className="workspace-name-hint">{mode === 'rename' ? <><Icon name="check" className="size-3.5 shrink-0" /><span>Renaming won’t affect files or member access</span></> : 'You can change this name later and invite people when you’re ready.'}</p>
      </div>
      <footer className="workspace-name-footer">
        {!setup && <button type="button" className="workspace-name-cancel" onClick={close} disabled={saving}>Cancel</button>}
        <button type="submit" className="workspace-name-save" disabled={saving || !trimmed}>{saving ? 'Saving…' : mode === 'create' ? 'Create workspace' : setup ? 'Save and continue' : 'Save changes'}<span aria-hidden="true">→</span></button>
      </footer>
    </form>
  </dialog>, document.body);
}
