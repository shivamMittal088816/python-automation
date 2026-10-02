import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Icon } from '../common/Presentation';
import { generateInvitation } from '../../services/invitations/api';
import './invite-workflow.css';

const workflows = [
  { value: 'mapping', title: 'Mapping', description: 'Match and review student records.', icon: 'grid' },
  { value: 'bulk', title: 'Bulk registration', description: 'Prepare student registration files.', icon: 'file' },
  { value: 'both', title: 'Both workflows', description: 'Share mapping and bulk registration.', icon: 'mail' },
];

export function InviteWorkflowDialog({ workflow, onClose }) {
  const dialog = useRef(null);
  const linkInput = useRef(null);
  const titleId = useId();
  const descriptionId = useId();
  const [role, setRole] = useState('editor');
  const [selectedWorkflow, setSelectedWorkflow] = useState(workflow);
  const [invitationLink, setInvitationLink] = useState('');
  const [copyStatus, setCopyStatus] = useState('');
  const [generating, setGenerating] = useState(false);
  const pending = useRef(false);

  useEffect(() => {
    setInvitationLink('');
    setCopyStatus('');
  }, [role, selectedWorkflow]);

  async function generateLink() {
    if (pending.current) return;
    pending.current = true;
    setGenerating(true);
    setInvitationLink('');
    setCopyStatus('');
    try {
      const result = await generateInvitation({
        workflow: selectedWorkflow === 'bulk' ? 'bulk_registration' : selectedWorkflow,
        permission: role,
      });
      setInvitationLink(result.invitation_url);
      setCopyStatus('Link ready to copy.');
    } catch (error) {
      setInvitationLink('');
      setCopyStatus(error.message || 'Could not generate the invitation link.');
    } finally {
      pending.current = false;
      setGenerating(false);
    }
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(invitationLink);
      setCopyStatus('Link copied');
    } catch {
      linkInput.current?.focus();
      linkInput.current?.select();
      setCopyStatus('Could not copy automatically. Copy the selected link manually.');
    }
  }

  useEffect(() => {
    const element = dialog.current;
    element.showModal();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      element.close();
      document.body.style.overflow = previousOverflow;
    };
  }, []);

  return createPortal(
    <dialog ref={dialog} className="invite-dialog" aria-labelledby={titleId} aria-describedby={descriptionId}
      onCancel={onClose} onClose={onClose} onClick={event => { if (event.target === event.currentTarget) onClose(); }}>
      <div className="invite-surface">
        <header className="invite-header">
          <span className="invite-header-icon"><Icon name="mail" className="size-6" /></span>
          <button type="button" className="invite-close" aria-label="Close invitation" onClick={onClose}>
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="m6 6 12 12M18 6 6 18" /></svg>
          </button>
          <p className="invite-eyebrow">WORKSPACE COLLABORATION</p>
          <h2 id={titleId}>Invite someone to your workflow</h2>
          <p id={descriptionId}>Choose the workflow options, then generate a link to copy and share.</p>
        </header>

        <div className="invite-body">
          <label className="invite-link-label" htmlFor={`${titleId}-link`}>Invitation link</label>
          <div className="invite-link-row">
            <input ref={linkInput} id={`${titleId}-link`} type="text" readOnly value={invitationLink}
              placeholder="Generate a link using the options below" className="invite-link-input"
              onFocus={event => event.target.select()} />
            <button type="button" className="invite-copy" aria-label="Copy invitation link" title="Copy invitation link"
              disabled={generating || !invitationLink} onClick={copyLink}><Icon name="copy" className="size-4" /></button>
          </div>
          <p className="invite-copy-status" role="status">{copyStatus || (invitationLink ? 'Link ready to copy.' : 'Choose your options and select Generate invitation link.')}</p>

          <fieldset className="invite-fieldset" disabled={generating}>
            <legend>Default role <span>Choose how they can participate.</span></legend>
            <div className="invite-role-grid">
              {[
                { value: 'editor', title: 'Editor', description: 'Collaborate on files and workflow settings.' },
                { value: 'viewer', title: 'Viewer', description: 'View shared workflows and results.' },
              ].map(option => <label key={option.value} className={`invite-choice invite-role ${role === option.value ? 'is-selected' : ''}`}>
                <input type="radio" name="invite-role" value={option.value} checked={role === option.value} onChange={() => setRole(option.value)} />
                <span><strong>{option.title}</strong><small>{option.description}</small></span>
                {option.value === 'editor' && <span className="invite-recommended">Default</span>}
              </label>)}
            </div>
          </fieldset>

          <fieldset className="invite-fieldset" disabled={generating}>
            <legend>Workflow access <span>Select one workflow or share both.</span></legend>
            <div className="invite-workflow-grid">
              {workflows.map(option => <label key={option.value} className={`invite-choice invite-workflow ${selectedWorkflow === option.value ? 'is-selected' : ''}`}>
                <div className="invite-workflow-top"><span className="invite-option-icon"><Icon name={option.icon} className="size-4" /></span>
                  <input type="radio" name="invite-workflow" value={option.value} checked={selectedWorkflow === option.value} onChange={() => setSelectedWorkflow(option.value)} /></div>
                <strong>{option.title}</strong><small>{option.description}</small>
              </label>)}
            </div>
          </fieldset>

          <div className="invite-summary"><span className="invite-summary-label">INVITATION SUMMARY</span>
            <p><strong>{role === 'editor' ? 'Editor' : 'Viewer'}</strong><span aria-hidden="true"> · </span>
              {selectedWorkflow === 'bulk' ? 'Bulk registration' : selectedWorkflow === 'both' ? 'Mapping + bulk registration' : 'Mapping'}
            </p>
          </div>
        </div>

        <footer className="invite-footer">
          <p><Icon name="info" className="size-4" /><span>Invitation links expire after 72 hours and can be used once.</span></p>
          <div><button type="button" className="invite-cancel" onClick={onClose}>Cancel</button>
            <button type="button" className="invite-send" disabled={generating} onClick={generateLink}><Icon name="link" className="size-4" />{generating ? 'Generating…' : 'Generate invitation link'}</button></div>
        </footer>
      </div>
    </dialog>, document.body,
  );
}
