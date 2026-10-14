import { useEffect, useState } from 'react';
import { ConfirmClearFile } from '../../components/common/ConfirmClearFile';
import { rollbackApi } from '../../services/rollbackApi';
import { RollbackInputPreview } from './RollbackInputPreview';
import { RollbackDumpPreview } from './RollbackDumpPreview';
import { ConfirmRollback } from './ConfirmRollback';
import { RegistrationSanityCheck } from '../BulkRegistration/components/RegistrationSanityCheck';
import '../BulkRegistration/bulk-registration.css';
import './rollback.css';

export function RollbackPage() {
  const [schoolIndex, setSchoolIndex] = useState('');
  const [school, setSchool] = useState(null);
  const [file, setFile] = useState(null);
  const [dump, setDump] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [sanityResult, setSanityResult] = useState(null);
  const [rollbackNotice, setRollbackNotice] = useState('');
  const [rollbackPreview, setRollbackPreview] = useState(null);

  useEffect(() => {
    let active = true;
    setBusy('restore');
    rollbackApi.getWorkspace()
      .then(result => {
        if (!active) return;
        setFile(result.file);
        setSchool(result.school);
        setDump(result.dump);
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
    setSanityResult(null);
    setRollbackNotice('');
    setRollbackPreview(null);
    setSchool(null);
    try {
      const result = await rollbackApi.verifySchool(index);
      setSchool(result.school);
      setDump(result.dump);
      setSchoolIndex(result.school.school_index);
    } catch (requestError) {
      setDump(null);
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
    setSanityResult(null);
    setRollbackNotice('');
    setRollbackPreview(null);
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
    setSanityResult(null);
    setRollbackNotice('');
    setRollbackPreview(null);
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

  async function showDumpPage(page) {
    if (busy) return;
    setBusy('dump');
    setError('');
    try {
      setDump(await rollbackApi.dumpPage(page));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy('');
    }
  }

  async function downloadDump(format) {
    if (busy || !dump) return;
    setBusy('download');
    setError('');
    try {
      await rollbackApi.downloadDump(format);
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
    setSanityResult(null);
    setRollbackNotice('');
    setRollbackPreview(null);
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
    setSanityResult(null);
    setRollbackNotice('');
    setRollbackPreview(null);
    try {
      await rollbackApi.clearSchool();
      setSchoolIndex('');
      setSchool(null);
      setDump(null);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy('');
    }
  }

  async function checkInput() {
    const result = await rollbackApi.sanityCheck();
    setSanityResult(result);
    return result;
  }

  async function runSanityCheck() {
    if (busy || !file) return;
    setBusy('sanity');
    setError('');
    setSanityResult(null);
    try {
      await checkInput();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy('');
    }
  }

  async function performRollback() {
    if (busy || !school || !file) return;
    setBusy('rollback');
    setError('');
    setSanityResult(null);
    setRollbackNotice('');
    try {
      const result = await checkInput();
      if (!result.valid) throw new Error(result.message);
      setRollbackPreview(await rollbackApi.previewChanges());
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy('');
    }
  }

  async function commitRollback() {
    if (busy || !rollbackPreview) return;
    setBusy('rollback');
    setError('');
    try {
      const result = await rollbackApi.run(rollbackPreview.preview_token);
      setRollbackNotice(result.message);
      setRollbackPreview(null);
    } catch (requestError) {
      setError(requestError.message);
      setRollbackPreview(null);
    } finally {
      setBusy('');
    }
  }

  const fallbackRules = [
    ['Class', 'Current class', 'Current class − 1', 'Moves the student down by one stored class level.'],
    ['Package', '14', '12', 'Changes the user from package 14 to package 12.'],
    ['Account', 'Active', 'Inactive', 'Sets user_activated from 1 to 0, which marks the account as inactive.'],
    ['Subscription', 'Subscribed', 'Unsubscribed', 'Sets user_subscribed from 1 to 0, which removes the subscribed status.'],
    ['Subscription date', 'Current date', '01 Apr 2025', 'Replaces the existing subscription date with the rollback date.'],
  ];

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
              <input id="rollback-school-index" required pattern="[0-9]+" inputMode="numeric" placeholder="Enter school number" disabled={!!busy} value={schoolIndex} onChange={event => { setSchoolIndex(event.target.value); setSchool(null); setDump(null); setError(''); setSanityResult(null); setRollbackNotice(''); }} />
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

        <RollbackDumpPreview dump={dump} school={school} busy={busy} onPage={showDumpPage} onDownload={downloadDump} />

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
      <RegistrationSanityCheck
        source={file}
        busy={!!busy}
        result={sanityResult}
        onCheck={runSanityCheck}
        footnote="Rollback checks supported headers and verifies that every record has a unique user_id."
        notice={<div className="rollback-requirement" role="note" aria-label="Required file check">
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 9v4M12 17h.01" />
            <path d="M10.3 3.7 2.4 17.4A2 2 0 0 0 4.1 20h15.8a2 2 0 0 0 1.7-2.6L13.7 3.7a2 2 0 0 0-3.4 0Z" />
          </svg>
          <p><strong>Required for rollback:</strong> The <code>user_id</code> header must be present because it is the unique identifier for each record.</p>
        </div>}
      />
      <section className="bulk-card rollback-action" aria-labelledby="rollback-action-title">
        <div className="bulk-section-title">
          <span className="bulk-step">04</span>
          <div>
            <h2 id="rollback-action-title">Perform rollback</h2>
            <p>Review the verified school, database dump, and uploaded input before continuing.</p>
          </div>
        </div>
        <button
          className="bulk-button bulk-primary"
          type="button"
          disabled={!!busy || !school || !file}
          onClick={performRollback}
        >{busy === 'rollback' ? 'Analyzing…' : 'Analyze rollback changes'}</button>
        {rollbackPreview && <div className="rollback-analysis" role="status">
          <div className="rollback-analysis-header">
            <div><strong>Change analysis</strong><p>No database changes have been committed.</p></div>
            <span className="rollback-safe-badge">Preview only</span>
          </div>
          <div className="rollback-impact">
            <div className="rollback-impact-total"><span>Users that will be updated</span><strong>{rollbackPreview.changed_count.toLocaleString()}</strong><p>Only users absent from the uploaded sheet.</p></div>
            <div className="rollback-impact-equation" aria-label="Rollback user calculation">
              <div><strong>{(rollbackPreview.fallback_count + rollbackPreview.supplied_matched).toLocaleString()}</strong><span>Eligible package-14 users</span></div>
              <b>−</b>
              <div><strong>{rollbackPreview.supplied_matched.toLocaleString()}</strong><span>Protected by sheet</span></div>
              <b>=</b>
              <div className="is-result"><strong>{rollbackPreview.fallback_count.toLocaleString()}</strong><span>Will be updated</span></div>
            </div>
          </div>
          {!!rollbackPreview.missing_ids?.length && <details className="rollback-missing"><summary>Review missing supplied IDs</summary><p>{rollbackPreview.missing_ids.join(', ')}</p></details>}
          <div className="rollback-change-preview">
            <div className="rollback-preview-toolbar">
              <div><h3>Changes applied to those users</h3><p>These five values are updated together.</p></div>
            </div>
            <div className="rollback-rule-list">{fallbackRules.map(([label, before, after, description], index) => <div className="rollback-rule-item" key={label}>
              <span className="rollback-rule-number">{index + 1}</span><div><strong>{label}</strong><p><span>{before}</span><b aria-hidden="true">→</b><em>{after}</em></p><small>{description}</small></div>
            </div>)}</div>
          </div>
          <div className="rollback-commit-row"><div><strong>Ready to apply?</strong><p>This updates {rollbackPreview.changed_count.toLocaleString()} database records. Sheet users remain unchanged.</p></div><ConfirmRollback affectedCount={rollbackPreview.changed_count} excludedCount={rollbackPreview.supplied_matched} disabled={!!busy} onConfirm={commitRollback} /></div>
        </div>}
        {rollbackNotice && <p className="rollback-action-notice" role="status">{rollbackNotice}</p>}
      </section>
    </div>
  </main>;
}
