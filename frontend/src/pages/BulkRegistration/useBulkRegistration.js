import { useRef, useState } from 'react';
import { bulkRegistrationApi } from '../../services/bulkRegistrationApi';
import { useBulkRegistrationWorkspace } from '../../hooks/useBulkRegistrationWorkspace';

export function useBulkRegistration() {
  const { state, ready, storageError, replace, edit: editState, refresh, beginOperation } = useBulkRegistrationWorkspace();
  const { path, file, source, schoolIndex, school, output, outputVerified } = state;
  const [working, setWorking] = useState(false);
  const busy = working || !ready;
  const [error, setError] = useState('');
  const [outputVerificationResult, setOutputVerificationResult] = useState(null);
  const [sanityResult, setSanityResult] = useState(null);
  const verificationKey = `${state.workspace_id}:${state.revision}`;
  const currentVerificationKey = useRef(verificationKey);
  currentVerificationKey.current = verificationKey;
  const sanity = sanityResult?.key === verificationKey ? sanityResult.result : null;
  const outputVerification = outputVerificationResult?.key === verificationKey
    ? outputVerificationResult.verification : null;
  const usernameChanges = outputVerificationResult?.key === verificationKey
    ? outputVerificationResult.usernameChanges : [];
  const schoolValid = school?.school_index === schoolIndex.trim();
  const pending = useRef(false);

  function edit(patch) {
    setError('');
    editState(patch);
  }

  async function handleError(err) {
    setError(err.message);
    if (err.status === 409) await refresh();
  }

  async function runMutation(operation, committed = []) {
    if (pending.current || !ready) return;
    pending.current = true; setWorking(true); setError('');
    const origin = beginOperation();
    try {
      const result = await operation(state.revision);
      replace(result, { origin, committed });
    } catch (err) { await handleError(err); }
    finally { pending.current = false; setWorking(false); }
  }

  async function verifySchool(event) {
    event.preventDefault();
    await runMutation(revision => bulkRegistrationApi.verifySchool(schoolIndex.trim(), revision),
      ['schoolIndex', 'school', 'output']);
  }

  function selectSheet(sheet) {
    if (!source || busy) return;
    runMutation(revision => bulkRegistrationApi.selectSheet(sheet, revision));
  }

  async function convert(format = 'preview', page = 1) {
    if (pending.current || !schoolValid || !source || !ready) return;
    pending.current = true; setWorking(true); setError('');
    const origin = beginOperation();
    try {
      const selectedSheet = format === 'preview'
        ? (page === 1 ? file?.sheet : output?.sheet !== undefined ? output.sheet : file?.sheet)
        : output?.sheet !== undefined ? output.sheet : file?.sheet;
      const result = await bulkRegistrationApi.convert({
        schoolIndex: schoolIndex.trim(), format, page, sheet: selectedSheet, revision: state.revision,
      });
      if (format === 'preview') {
        replace(result, { origin });
        setOutputVerificationResult(null);
      }
      else {
        const blob = await result.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a'); link.href = url;
        link.download = `bulk-registration-${schoolIndex.trim()}.${format}`;
        document.body.appendChild(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        await refresh();
      }
    } catch (err) { await handleError(err); }
    finally { pending.current = false; setWorking(false); }
  }

  async function showOutputPage(page) {
    if (pending.current || !ready) return;
    pending.current = true; setWorking(true); setError('');
    const origin = beginOperation();
    try { replace(await bulkRegistrationApi.outputPage(page), { origin, announce: false }); }
    catch (err) { await handleError(err); }
    finally { pending.current = false; setWorking(false); }
  }

  async function showInputPage(page) {
    if (pending.current || !source || !ready) return;
    pending.current = true; setWorking(true); setError('');
    const origin = beginOperation();
    try { replace(await bulkRegistrationApi.inputPage(page), { origin, announce: false }); }
    catch (err) { await handleError(err); }
    finally { pending.current = false; setWorking(false); }
  }

  async function verifyOutput() {
    if (pending.current || !output || !ready) return;
    pending.current = true; setWorking(true); setError('');
    setOutputVerificationResult(null);
    const origin = beginOperation();
    try {
      const result = await bulkRegistrationApi.verifyOutput(state.revision);
      replace(result.workspace, { origin });
      const key = `${result.workspace.workspace_id}:${result.workspace.revision}`;
      setOutputVerificationResult({
        key, verification: result.verification, usernameChanges: result.username_changes || [],
      });
    }
    catch (err) { await handleError(err); }
    finally { pending.current = false; setWorking(false); }
  }

  async function runSanityCheck() {
    if (pending.current || !source || !ready) return;
    pending.current = true; setWorking(true); setError('');
    setSanityResult(null);
    const key = verificationKey;
    try {
      const result = await bulkRegistrationApi.sanityCheck(state.revision);
      if (currentVerificationKey.current === key) setSanityResult({ key, result });
    } catch (err) { await handleError(err); }
    finally { pending.current = false; setWorking(false); }
  }

  function upload(files) {
    if (pending.current || !files.length) return;
    if (files.length !== 1 || !/\.(csv|xlsx)$/i.test(files[0].name)) {
      setError('Choose one CSV or XLSX file.'); return;
    }
    runMutation(revision => bulkRegistrationApi.uploadFile(files[0], revision), ['path']);
  }

  async function clearWorkspace(resetAll = false) {
    if (pending.current || !ready) return;
    pending.current = true; setWorking(true); setError('');
    const origin = beginOperation();
    try {
      const result = await (resetAll
        ? bulkRegistrationApi.resetWorkspace(state.revision)
        : bulkRegistrationApi.clearFile(state.revision));
      replace(result, { origin, reset: resetAll, committed: ['path'] });
    } catch (err) { await handleError(err); }
    finally { pending.current = false; setWorking(false); }
  }

  return {
    path, file, source, schoolIndex, school, output, outputVerified, outputVerification, usernameChanges,
    ready, storageError, working, busy, error, schoolValid, sanity, runSanityCheck,
    edit,
    load: (_endpoint, body) => runMutation(revision => bulkRegistrationApi.loadPath(body.path, revision), ['path']),
    verifySchool, selectSheet, convert, showOutputPage, showInputPage, verifyOutput, upload, clearWorkspace,
  };
}
