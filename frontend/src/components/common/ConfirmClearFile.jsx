import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import './confirm-clear-file.css';

export function ConfirmClearFile({ file, disabled, onConfirm, label = 'Clear file', className = '' }) {
  const [open, setOpen] = useState(false);
  const dialog = useRef(null);
  const titleId = useId();
  const descriptionId = useId();
  // Do not confirm removal of a replacement received from another tab.
  useEffect(() => { setOpen(false); }, [file]);
  useEffect(() => {
    if (open) dialog.current?.showModal();
    else dialog.current?.close();
  }, [open]);

  return <>
    <button type="button" className={className} disabled={disabled} aria-label={label}
      onClick={() => setOpen(true)}>Clear file</button>
    {createPortal(
      <dialog ref={dialog} className="clear-file-dialog" aria-labelledby={titleId}
        aria-describedby={descriptionId} onCancel={() => setOpen(false)} onClose={() => setOpen(false)}>
        <h2 id={titleId}>Clear this file?</h2>
        <p className="clear-file-name">{file?.name}</p>
        <p id={descriptionId}>This removes the loaded file and its dependent results from the workspace in all synced tabs. The original file and database records stay unchanged.</p>
        <div className="clear-file-actions">
          <button type="button" autoFocus onClick={() => setOpen(false)}>Cancel</button>
          <button type="button" className="clear-file-confirm" disabled={disabled || !open}
            onClick={() => { setOpen(false); onConfirm(); }}>Confirm</button>
        </div>
      </dialog>, document.body,
    )}
  </>;
}
