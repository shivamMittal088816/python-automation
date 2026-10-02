import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Icon } from '../common/Presentation';
import { joinInvitation } from '../../services/invitations/api';
import { invitationToken } from './utils/invitationToken';
import './invite-workflow.css';


export function JoinWorkflowDialog({ onClose, initialCode = '' }) {
  const dialog = useRef(null);
  const codeInput = useRef(null);
  const titleId = useId();
  const descriptionId = useId();
  const inputId = useId();
  const helpId = useId();
  const [code, setCode] = useState(initialCode);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState('');
  const pending = useRef(false);
  const active = useRef(true);

  async function join(event) {
    event.preventDefault();
    if (pending.current) return;
    const token = invitationToken(code);
    if (!token) {
      setError('Enter a valid invitation code or link.');
      return;
    }
    pending.current = true;
    setJoining(true);
    setError('');
    try {
      const result = await joinInvitation(token);
      // Reload so the workflow providers restore the account's new selection.
      if (active.current) window.location.assign(result.destination);
    } catch (err) {
      if (active.current) setError(err.message || 'Could not join the workflow. Please try again.');
    } finally {
      pending.current = false;
      if (active.current) setJoining(false);
    }
  }

  useEffect(() => {
    const element = dialog.current;
    active.current = true;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    element.showModal();
    codeInput.current?.focus();
    document.body.style.overflow = 'hidden';
    return () => {
      active.current = false;
      element.close();
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus();
    };
  }, []);

  return createPortal(
    <dialog ref={dialog} className="invite-dialog join-dialog" aria-labelledby={titleId} aria-describedby={descriptionId}
      onCancel={event => { if (joining) event.preventDefault(); else onClose(); }} onClose={onClose}
      onClick={event => { if (!joining && event.target === event.currentTarget) onClose(); }}>
      <form className="invite-surface" onSubmit={join}>
        <header className="invite-header">
          <span className="invite-header-icon"><Icon name="link" className="size-6" /></span>
          <button type="button" className="invite-close" aria-label="Close invitation code dialog" onClick={onClose} disabled={joining}>
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="m6 6 12 12M18 6 6 18" /></svg>
          </button>
          <p className="invite-eyebrow">WORKSPACE COLLABORATION</p>
          <h2 id={titleId}>Join with invitation code</h2>
          <p id={descriptionId}>Have an invitation? Paste the code or link shared with you.</p>
        </header>
        <div className="invite-body">
          <label className="invite-link-label" htmlFor={inputId}>Invitation code</label>
          <input ref={codeInput} id={inputId} type="text" className="invite-link-input join-code-input"
            value={code} onChange={event => { setCode(event.target.value); setError(''); }} disabled={joining}
            placeholder="Paste your invitation code or link" autoComplete="off" autoCapitalize="none"
            spellCheck={false} aria-describedby={helpId} aria-invalid={Boolean(error)} maxLength={2048} />
          <p id={helpId} className="join-code-help">Paste the full invitation link or just its code.</p>
          {error && <p role="alert" className="join-code-error">{error}</p>}
          <div className="join-code-note"><Icon name="info" className="size-4" />
            <p>Invitation codes expire after 72 hours and can be used once.</p>
          </div>
        </div>
        <footer className="invite-footer">
          <p>{joining ? 'Opening your shared workspace…' : 'Your access is set by the invitation owner.'}</p>
          <div>
            <button type="button" className="invite-cancel" onClick={onClose} disabled={joining}>Cancel</button>
            <button type="submit" className="invite-send" disabled={joining || !code.trim()}><Icon name="link" className="size-4" />{joining ? 'Joining…' : 'Join workflow'}</button>
          </div>
        </footer>
      </form>
    </dialog>, document.body,
  );
}
