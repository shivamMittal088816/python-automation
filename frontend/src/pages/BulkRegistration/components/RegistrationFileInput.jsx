import { useState } from 'react';
import { ConfirmClearFile } from '../../../components/common/ConfirmClearFile';

export function RegistrationFileInput({ path, file, busy, load, upload, selectSheet, edit }) {
  const [dragging, setDragging] = useState(false);

  return (
    <section aria-label="Load registration file" className="bulk-card">
      <div className="bulk-section-title">
        <span className="bulk-step">02</span>
        <div>
          <h2>Add your input file</h2>
          <p>Upload a spreadsheet or use a file path.</p>
        </div>
        <span className="bulk-format">CSV / XLSX</span>
      </div>
      <label onDragOver={event => { event.preventDefault(); if (!busy) setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); upload(event.dataTransfer.files); }} className={`bulk-drop ${dragging ? 'is-dragging' : ''} ${busy ? 'is-disabled' : ''}`}>
        <svg aria-hidden="true" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 16V3m-5 5 5-5 5 5M4 15v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5" />
        </svg>
        <span>
          <strong>Drag and drop your file here</strong>
          <span className="bulk-drop-hint">or click to browse &middot; CSV or XLSX</span>
        </span>
        <input type="file" aria-label="Upload registration file" accept=".csv,.xlsx" disabled={busy} onChange={event => { upload(event.target.files); event.target.value = ''; }} />
        </label>
        <form className="bulk-inline-form bulk-path" onSubmit={event => { event.preventDefault(); load('/bulk-reg/files/path', { path }); }}>
          <div className="bulk-field">
            <label htmlFor="bulk-file-path">Or use a file path</label>
            <input id="bulk-file-path" aria-label="File path" required disabled={busy} value={path} onChange={event => edit({ path: event.target.value })} placeholder="C:\Users\USER\Downloads\registrations.xlsx" />
            </div>
            <button disabled={busy || !path.trim()} className="bulk-button bulk-secondary">Load file</button>
          </form>
          <p className="bulk-hint">Use a path on the computer running the backend. Path loading must be enabled.</p>
          {file && <div className="bulk-file-status">
            <div>
              <strong>{file.name}</strong>
              <span role="status">{file.row_count} rows &middot; {file.columns.length} columns &middot; File loaded</span>
            </div>
            <ConfirmClearFile file={file} disabled={busy} className="bulk-text-button"
              onConfirm={() => edit({ file: null, source: null, output: null })} />
          </div>}
          {!!file?.sheets?.length && <div className="bulk-field bulk-sheet-field">
            <label htmlFor="bulk-working-sheet">Working sheet</label>
            <select id="bulk-working-sheet" disabled={busy} value={file.sheet} onChange={event => selectSheet(event.target.value)}>
              {file.sheets.map(sheet => <option key={sheet} value={sheet}>{sheet}</option>)}
            </select>
            <p className="bulk-hint">New previews use this worksheet. Existing results stay until you generate again.{file.row_count === 0 ? ' This sheet is empty; select another tab.' : ''}</p>
          </div>}
        </section>
  );
}
