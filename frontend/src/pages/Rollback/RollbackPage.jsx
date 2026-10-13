import { useEffect, useState } from 'react';
import { ConfirmClearFile } from '../../components/common/ConfirmClearFile';
import { rollbackApi } from '../../services/rollbackApi';
import { RollbackInputPreview } from './RollbackInputPreview';
import '../BulkRegistration/bulk-registration.css';
import './rollback.css';

export function RollbackPage() {
  const [schoolIndex, setSchoolIndex] = useState('');
  const [school, setSchool] = useState(null);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setBusy('restore');
    rollbackApi.getWorkspace()
      .then(result => {
        if (!active) return;
        setFile(result.file);
        setSchool(result.school);
        setSchoolIndex(result.school?.school_index || '');
      })
      .catch(requestError => { if (active) setError(requestError.message); })
      .finally(() => { if (active) setBusy(''); });
    return () => { active = false; };
  }, []);

  async function verifySchool(event) {
    event.preventDefault();
    const index = schoolIndex.trim();
    if (!/^[0-9]+$/.test(index) || busy) return;
    setBusy('school');
    setError('');
    setSchool(null);
    try {
      const result = await rollbackApi.verifySchool(index);
      setSchool(result.school);
      setSchoolIndex(result.school.school_index);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy('');
    }
  }

  async function upload(files, sheet) {
    if (busy || !files?.length) return;
    const selected = files[0];
    if (files.length !== 1 || !/\.(csv|xlsx)$/i.test(selected.name)) {
      setError('Choose one CSV or XLSX file.');
      return;
    }
    setBusy('file');
    setError('');
    try {
      setFile(await rollbackApi.uploadFile(selected, sheet));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy('');
    }
  }

  const chooseFile = event => {
    upload(event.target.files);
    event.target.value = '';
  };

  async function selectSheet(event) {
    if (busy) return;
    setBusy('file');
    setError('');
    try {
      setFile(await rollbackApi.selectSheet(event.target.value));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy('');
    }
  }

  async function showInputPage(page) {
    if (busy) return;
    setBusy('preview');
    setError('');
    try {
      setFile(await rollbackApi.inputPage(page));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy('');
    }
  }

  async function clearFile() {
    if (busy) return;
    setBusy('file');
    setError('');
    try {
      await rollbackApi.clearFile();
      setFile(null);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy('');
    }
  }

  async function clearSchool() {
    if (busy) return;
    setBusy('school');
    setError('');
    try {
      await rollbackApi.clearSchool();
      setSchoolIndex('');
      setSchool(null);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy('');
    }
  }

  return <main className="bulk-page rollback-page">
    <div className="bulk-shell rollback-shell">
      <header className="bulk-header rollback-header">
        <div>
          <p className="bulk-eyebrow">ROLLBACK ACTIVITY</p>
          <h1>Prepare rollback file</h1>
          <p className="bulk-subtitle">Verify the school and upload the CSV or Excel file you want to use.</p>
        </div>
      </header>

      {error && <p className="bulk-error rollback-error" role="alert">{error}</p>}

      <div className="rollback-grid">
        <section className="bulk-card" aria-labelledby="rollback-school-title">
          <div className="bulk-section-title">
            <span className="bulk-step">01</span>
            <div>
              <h2 id="rollback-school-title">Verify school</h2>
              <p>Enter the school number to fetch its name from the database.</p>
            </div>
            {school && <span className="bulk-badge">Verified</span>}
          </div>
          <form className="bulk-inline-form" onSubmit={verifySchool}>
            <div className="bulk-field">
              <label htmlFor="rollback-school-index">School number</label>
              <input id="rollback-school-index" required pattern="[0-9]+" inputMode="numeric" placeholder="Enter school number" disabled={!!busy} value={schoolIndex} onChange={event => { setSchoolIndex(event.target.value); setSchool(null); setError(''); }} />
            </div>
            <div className="rollback-school-actions">
              <button className="bulk-button bulk-primary" disabled={!!busy || !/^[0-9]+$/.test(schoolIndex.trim())} type="submit">{busy === 'school' ? 'Verifying…' : 'Verify school'}</button>
              <button className="bulk-button bulk-secondary" disabled={!!busy || (!schoolIndex && !school)} type="button" onClick={clearSchool}>Clear school</button>
            </div>
          </form>
          {school && <div className="bulk-verified">
            <p role="status">School verified</p>
            <label htmlFor="rollback-school-name">School name</label>
            <input id="rollback-school-name" readOnly value={school.school_name} />
          </div>}
        </section>

        <section className="bulk-card bulk-file-card" aria-labelledby="rollback-file-title">
          <div className="bulk-section-title">
            <span className="bulk-step">02</span>
            <div>
              <h2 id="rollback-file-title">Upload rollback file</h2>
              <p>Select one file from your device. CSV and XLSX files are accepted.</p>
            </div>
            <span className="bulk-format">CSV / XLSX</span>
          </div>
          {!file ? <label onDragOver={event => { event.preventDefault(); if (!busy) setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); upload(event.dataTransfer.files); }} className={`bulk-drop ${dragging ? 'is-dragging' : ''} ${busy ? 'is-disabled' : ''}`}>
            <svg aria-hidden="true" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M12 16V3m-5 5 5-5 5 5M4 15v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5" /></svg>
            <span><strong>{busy === 'file' ? 'Uploading file…' : 'Drop your file here'}</strong><span className="bulk-drop-hint">or click to browse your device</span></span>
            <span className="bulk-drop-type">CSV or XLSX</span>
            <input type="file" aria-label="Upload rollback file" accept=".csv,.xlsx" disabled={!!busy} onChange={chooseFile} />
          </label> : <div className="bulk-loaded-file">
            <div className="bulk-loaded-file-main">
              <span className="bulk-file-icon" aria-hidden="true"><svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/></svg></span>
              <div className="bulk-loaded-file-copy"><span className="bulk-loaded-label">File uploaded</span><strong>{file.name}</strong><span role="status">{file.row_count.toLocaleString()} rows <i aria-hidden="true">&middot;</i> {file.columns.length} columns</span></div>
              <div className="bulk-file-actions">
                <label className={`bulk-button bulk-secondary bulk-replace-file ${busy ? 'is-disabled' : ''}`}>Replace<input type="file" aria-label="Replace rollback file" accept=".csv,.xlsx" disabled={!!busy} onChange={chooseFile} /></label>
                <ConfirmClearFile file={file} disabled={!!busy} className="bulk-text-button" onConfirm={clearFile} description="This removes the uploaded rollback file and its preview from this browser workspace. The original file and database records stay unchanged." />
              </div>
            </div>
            {!!file.sheets?.length && <div className="rollback-sheet">
              <div><label htmlFor="rollback-sheet">Worksheet</label><p>Select the Excel tab to use for rollback.</p></div>
              <select id="rollback-sheet" disabled={!!busy} value={file.sheet || ''} onChange={selectSheet}>{file.sheets.map(sheet => <option key={sheet} value={sheet}>{sheet}</option>)}</select>
            </div>}
          </div>}
        </section>
      </div>
      <RollbackInputPreview file={file} busy={busy} onPage={showInputPage} />
    </div>
  </main>;
}
