import { useState } from 'react';
import { ConfirmClearFile } from '../../../components/common/ConfirmClearFile';

export function RegistrationFileInput({ path, file, busy, load, upload, selectSheet, edit, clearFile }) {
  const [dragging, setDragging] = useState(false);
  const chooseFile = event => { upload(event.target.files); event.target.value = ''; };

  return <section aria-label="Load registration file" className="bulk-card bulk-file-card">
    <div className="bulk-section-title">
      <span className="bulk-step">02</span>
      <div><h2>Add your input file</h2><p>Choose one spreadsheet to prepare for registration.</p></div>
      <span className="bulk-format">CSV / XLSX</span>
    </div>

    {!file ? <label onDragOver={event => { event.preventDefault(); if (!busy) setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); upload(event.dataTransfer.files); }} className={`bulk-drop ${dragging ? 'is-dragging' : ''} ${busy ? 'is-disabled' : ''}`}>
      <svg aria-hidden="true" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M12 16V3m-5 5 5-5 5 5M4 15v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5" /></svg>
      <span><strong>Drop your file here</strong><span className="bulk-drop-hint">or click to browse</span></span>
      <span className="bulk-drop-type">CSV or XLSX</span>
      <input type="file" aria-label="Upload registration file" accept=".csv,.xlsx" disabled={busy} onChange={chooseFile} />
    </label> : <div className="bulk-loaded-file">
      <div className="bulk-loaded-file-main">
        <span className="bulk-file-icon" aria-hidden="true"><svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/></svg></span>
        <div className="bulk-loaded-file-copy"><span className="bulk-loaded-label">File ready</span><strong>{file.name}</strong><span role="status">{file.row_count} rows <i aria-hidden="true">&middot;</i> {file.columns.length} columns</span></div>
        <div className="bulk-file-actions">
          <label className={`bulk-button bulk-secondary bulk-replace-file ${busy ? 'is-disabled' : ''}`}>Replace<input type="file" aria-label="Upload registration file" accept=".csv,.xlsx" disabled={busy} onChange={chooseFile} /></label>
          <ConfirmClearFile file={file} disabled={busy} className="bulk-text-button" onConfirm={() => clearFile()} />
        </div>
      </div>
      {!!file.sheets?.length && <div className="bulk-sheet-row">
        <div><label htmlFor="bulk-working-sheet">Working sheet</label><p>Choose the worksheet used for the next preview.</p></div>
        <select id="bulk-working-sheet" disabled={busy} value={file.sheet} onChange={event => selectSheet(event.target.value)}>{file.sheets.map(sheet => <option key={sheet} value={sheet}>{sheet}</option>)}</select>
        {file.row_count === 0 && <p className="bulk-sheet-warning">This sheet is empty. Select another worksheet.</p>}
      </div>}
    </div>}

    <details className="bulk-path-disclosure">
      <summary>Use a file path instead <span>For files on the backend computer</span></summary>
      <form className="bulk-inline-form bulk-path" onSubmit={event => { event.preventDefault(); load('/bulk-reg/files/path', { path }); }}>
        <div className="bulk-field"><label htmlFor="bulk-file-path">File path</label><input id="bulk-file-path" aria-label="File path" required disabled={busy} value={path} onChange={event => edit({ path: event.target.value })} placeholder="C:\Users\USER\Downloads\registrations.xlsx" /></div>
        <button disabled={busy || !path.trim()} className="bulk-button bulk-secondary">Load file</button>
      </form>
      <p className="bulk-hint">Path loading must be enabled on the backend.</p>
    </details>
  </section>;
}
