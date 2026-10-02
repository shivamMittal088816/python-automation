import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { deleteWorkspace } from '../../services/workspaces/api';
import './workspace-name.css';

export function WorkspaceDeleteDialog({ workspace, onClose, onDeleted, returnFocusRef }) {
  const dialog = useRef(null);
  const cancel = useRef(null);
  const pending = useRef(false);
  const active = useRef(true);
  const titleId = useId(), helpId = useId();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const element = dialog.current;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    active.current = true;
    element.showModal();
    cancel.current?.focus();
    document.body.style.overflow = 'hidden';
    return () => {
      active.current = false;
      element.close();
      document.body.style.overflow = previousOverflow;
      (returnFocusRef?.current?.querySelector('summary') || previousFocus)?.focus();
    };
  }, [returnFocusRef]);

  async function submit(event) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setSaving(true);
    setError('');
    try {
      const result = await deleteWorkspace(workspace.id);
      if (active.current) onDeleted(result);
    } catch (err) {
      if (active.current) setError(err.message || 'Could not delete the workspace. Please try again.');
    } finally {
      pending.current = false;
      if (active.current) setSaving(false);
    }
  }
  const close = () => { if (!pending.current) onClose(); };
  return createPortal(<dialog ref={dialog} className="workspace-name-dialog" aria-labelledby={titleId} aria-describedby={helpId}
    onCancel={event => { event.preventDefault(); close(); }}
    onClick={event => { if (event.target === event.currentTarget) close(); }}>
    <form onSubmit={submit}>
      <header className="workspace-name-header">
        <h2 id={titleId}>Delete workspace?</h2>
        <p id={helpId}>“{workspace.name}” will be removed from workspace lists. Everyone with access will lose access immediately.</p>
      </header>
      {error && <div className="workspace-name-body"><p className="workspace-name-error" role="alert">{error}</p></div>}
      <footer className="workspace-name-footer">
        <button ref={cancel} type="button" className="workspace-name-cancel" disabled={saving} onClick={close}>Cancel</button>
        <button type="submit" className="workspace-delete-confirm" disabled={saving}>{saving ? 'Deleting…' : 'Delete workspace'}</button>
      </footer>
    </form>
  </dialog>, document.body);
}
