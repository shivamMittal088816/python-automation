import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

export function ConfirmRollback({ affectedCount, excludedCount, disabled, onConfirm }) {
  const [open, setOpen] = useState(false);
  const dialog = useRef(null);
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    if (open) dialog.current?.showModal();
    else dialog.current?.close();
  }, [open]);

  return <>
    <button className="bulk-button bulk-primary" type="button" disabled={disabled}
      onClick={() => setOpen(true)}>Commit {affectedCount.toLocaleString()} changes</button>
    {createPortal(
      <dialog ref={dialog} className="rollback-confirm-dialog" aria-labelledby={titleId}
        aria-describedby={descriptionId} onCancel={() => setOpen(false)} onClose={() => setOpen(false)}>
        <div className="rollback-confirm-icon" aria-hidden="true">!</div>
        <div className="rollback-confirm-copy">
          <p className="rollback-confirm-eyebrow">Database update</p>
          <h2 id={titleId}>Commit rollback changes?</h2>
          <p id={descriptionId}>This action will immediately update live database records for the verified school.</p>
        </div>
        <div className="rollback-confirm-summary">
          <div><strong>{affectedCount.toLocaleString()}</strong><span>users will be updated</span></div>
          <div><strong>{excludedCount.toLocaleString()}</strong><span>sheet IDs remain unchanged</span></div>
        </div>
        <div className="rollback-confirm-warning"><strong>Please verify before continuing</strong><span>Package, activation, subscription, class, and subscription date values will be changed.</span></div>
        <div className="rollback-confirm-actions">
          <button type="button" autoFocus onClick={() => setOpen(false)}>Cancel</button>
          <button type="button" className="rollback-confirm-submit" disabled={disabled || !open}
            onClick={() => { setOpen(false); onConfirm(); }}>Yes, commit changes</button>
        </div>
      </dialog>, document.body,
    )}
  </>;
}
