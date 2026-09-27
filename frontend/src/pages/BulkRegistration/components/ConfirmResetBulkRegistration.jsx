import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import '../../../components/common/confirm-clear-file.css';


export function ConfirmResetBulkRegistration({ disabled, onConfirm }) {
  const [open, setOpen] = useState(false);
  const dialog = useRef(null);
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    if (open) dialog.current?.showModal();
    else dialog.current?.close();
  }, [open]);

  return <>
    <button type="button" className="bulk-text-button" disabled={disabled}
      onClick={() => setOpen(true)}>Reset bulk registration</button>
    {createPortal(
      <dialog ref={dialog} className="clear-file-dialog" aria-labelledby={titleId}
        aria-describedby={descriptionId} onCancel={() => setOpen(false)}
        onClose={() => setOpen(false)}>
        <h2 id={titleId}>Reset bulk registration?</h2>
        <p id={descriptionId}>This permanently removes the loaded file, verified school, generated outputs, and saved bulk-registration workspace from all synced tabs.</p>
        <div className="clear-file-actions">
          <button type="button" autoFocus onClick={() => setOpen(false)}>Cancel</button>
          <button type="button" className="clear-file-confirm" disabled={disabled || !open}
            onClick={() => { setOpen(false); onConfirm(); }}>Confirm</button>
        </div>
      </dialog>, document.body,
    )}
  </>;
}
