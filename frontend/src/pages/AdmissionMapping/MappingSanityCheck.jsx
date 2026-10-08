import { useEffect, useRef, useState } from 'react';
import { Alert } from '../../components/common/Controls';
import { useWorkspace } from '../../context/WorkspaceContext';
import { admissionMappingApi } from '../../services/admissionMappingApi';
import { RegistrationSanityCheck } from '../BulkRegistration/components/RegistrationSanityCheck';
import '../BulkRegistration/bulk-registration.css';

export function MappingSanityCheck({ sheet, nameColumn, admissionColumn }) {
  const { workspace, busy } = useWorkspace();
  const [result, setResult] = useState(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState('');
  const pending = useRef(null);
  useEffect(() => () => pending.current?.abort(), []);

  async function check() {
    pending.current?.abort();
    const controller = new AbortController();
    pending.current = controller;
    setChecking(true);
    setError('');
    setResult(null);
    try {
      const response = await admissionMappingApi.sanityCheck(
        { admission_school_sheet: sheet || null, school_name_col: nameColumn || null,
          school_admission_col: admissionColumn || null }, workspace.revision, controller.signal,
      );
      if (!controller.signal.aborted) setResult(response);
    } catch (failure) {
      if (!controller.signal.aborted) setError(failure.message);
    } finally {
      if (!controller.signal.aborted) setChecking(false);
    }
  }

  return <div aria-busy={checking}>
    <RegistrationSanityCheck source={workspace.files.school} busy={!!busy || checking}
      result={result} onCheck={check}
      footnote="Checks use the selected first-name column and recognized school headers. Optional fields are checked when supplied; classes accept names or positive numbers." />
    {checking && <p role="status" className="caption">Checking school records…</p>}
    {error && <Alert type="error">{error}</Alert>}
  </div>;
}
