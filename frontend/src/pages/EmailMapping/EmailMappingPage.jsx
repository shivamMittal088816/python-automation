import { PageHeader } from '../../components/common/Presentation';
import { useWorkspace } from '../../context/WorkspaceContext';
import { useRequest } from '../../hooks/useRequest';
import { ActionLink, Alert } from '../../components/common/Controls';
import { EmailForm } from './EmailForm';
export function EmailMappingPage() {
  const { workspace } = useWorkspace();
  return <div className="page-stack"><PageHeader title="Email mapping" description="Match remaining students using their email address and first name." /><ActionLink to="/admission_preview_page">Back to admission preview</ActionLink>{!Object.keys(workspace.exports.admission).length ? <Alert>First run admission mapping.</Alert> : workspace.email_ready ? <EmailSource key={workspace.workspace_id} /> : <Alert>There are no Not matched students to send to email mapping.</Alert>}</div>;
}
function EmailSource() {
  const { emailSourceKey, getEmailSourceMetadata } = useWorkspace();
  const request = useRequest(() => getEmailSourceMetadata(), [emailSourceKey]);
  return <>{request.error && <Alert type="error">{request.error}</Alert>}{request.data && <EmailForm source={request.data} />}</>;
}
