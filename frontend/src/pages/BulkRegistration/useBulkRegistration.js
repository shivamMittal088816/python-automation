import { useRef, useState } from 'react';
import { request } from '../../services/api';
import { useBulkRegistrationWorkspace } from '../../hooks/useBulkRegistrationWorkspace';

export function useBulkRegistration() {
  const { state, ready, storageError, update } = useBulkRegistrationWorkspace();
  const { path, file, source, schoolIndex, school, output } = state;
  const [working, setWorking] = useState(false);
  const busy = working || !ready;
  const [error, setError] = useState('');
  const schoolValid = school?.school_index === schoolIndex.trim();
  const pending = useRef(false);

  function edit(patch) {
    setError('');
    update(patch, undefined, true).catch(err => setError(err.message));
  }

  async function load(endpoint, body, preserveOutput = false) {
    if (pending.current || !ready) return;
    pending.current = true; setWorking(true); setError('');
    try {
      const revision = await update({}, state.revision);
      const result = await request(endpoint, { method: 'POST', body });
      await update({ file: result, output: preserveOutput && output ? { ...output, sheet: output.sheet !== undefined ? output.sheet : file?.sheet ?? null } : null, source: body instanceof FormData ? { file: body.get('file') } : { path: body.path } }, revision);
    } catch (err) { setError(err.message); }
    finally { pending.current = false; setWorking(false); }
  }

  async function verifySchool(event) {
    event.preventDefault();
    if (pending.current || !ready) return;
    pending.current = true; setWorking(true); setError('');
    try {
      const revision = await update({ school: null, output: null }, state.revision);
      const result = await request(`/bulk-reg/schools/${encodeURIComponent(schoolIndex.trim())}`);
      await update({ school: result }, revision);
    } catch (err) { setError(err.message); }
    finally { pending.current = false; setWorking(false); }
  }

  function selectSheet(sheet) {
    if (!source || busy) return;
    if (source.file) {
      const body = new FormData();
      body.append('file', source.file);
      body.append('sheet', sheet);
      load('/bulk-reg/files', body, true);
    } else load('/bulk-reg/files/path', { path: source.path, sheet }, true);
  }

  async function convert(format = 'preview') {
    if (pending.current || !schoolValid || !source || !ready) return;
    pending.current = true; setWorking(true); setError('');
    try {
      const revision = await update({}, state.revision);
      const body = new FormData();
      body.append('school_index', schoolIndex.trim());
      body.append('file_format', format);
      const selectedSheet = format === 'preview' ? file?.sheet : output?.sheet !== undefined ? output.sheet : file?.sheet;
      if (selectedSheet != null) body.append('sheet', selectedSheet);
      if (source.file) body.append('file', source.file); else body.append('path', source.path);
      const result = await request('/bulk-reg/convert', { method: 'POST', body, blob: format !== 'preview' });
      if (format === 'preview') await update({ output: { ...result, sheet: selectedSheet ?? null }, school: result.school }, revision);
      else {
        const blob = await result.blob();
        await update({}, revision);
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a'); link.href = url;
        link.download = `bulk-registration-${schoolIndex.trim()}.${format}`;
        document.body.appendChild(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
    } catch (err) { setError(err.message); }
    finally { pending.current = false; setWorking(false); }
  }

  function upload(files) {
    if (pending.current || !files.length) return;
    if (files.length !== 1 || !/\.(csv|xlsx)$/i.test(files[0].name)) {
      setError('Choose one CSV or XLSX file.'); return;
    }
    const body = new FormData(); body.append('file', files[0]);
    load('/bulk-reg/files', body);
  }

  return {
    path, file, source, schoolIndex, school, output,
    ready, storageError, working, busy, error, schoolValid,
    edit, load, verifySchool, selectSheet, convert, upload,
  };
}
