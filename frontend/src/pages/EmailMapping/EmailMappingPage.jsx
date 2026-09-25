import { PageHeader } from '../../components/common/Presentation';
import { useWorkspace } from '../../context/WorkspaceContext';
import { useRequest } from '../../hooks/useRequest';
import { Alert } from '../../components/common/Controls';
import { EmailForm } from './EmailForm';
import { admissionMappingApi } from '../../services/admissionMappingApi';
export function EmailMappingPage() {
  const { workspace } = useWorkspace();
  return <div className="page-stack"><PageHeader title="Email mapping" description="Match school-file students using their email address and first name." />{workspace.email_ready ? <EmailSource key={workspace.workspace_id} /> : <Alert>Load a school file first.</Alert>}</div>;
}
function EmailSource() {
  const { workspace, id, emailSourceKey, getEmailSourceMetadata } = useWorkspace();
  const request = useRequest(() => getEmailSourceMetadata(), [emailSourceKey]);
  const admissionVersion = workspace.export_versions?.admission?.['not_matched.xlsx'];
  const admission = useRequest(
    () => admissionVersion
      ? admissionMappingApi.results('admission', 'not_matched.xlsx', { page: 1, limit: 1 })
      : Promise.resolve(null),
    [id, admissionVersion],
  );
  return <>{request.error && <Alert type="error">{request.error}</Alert>}{admission.error && <Alert type="error">{admission.error}</Alert>}{request.data && <EmailForm schoolSource={request.data} admissionSource={admission.data} />}</>;
}
