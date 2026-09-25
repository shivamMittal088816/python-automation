import { PageHeader } from '../../components/common/Presentation';
import { useWorkspace } from '../../context/WorkspaceContext';
import { ActionLink, Alert } from '../../components/common/Controls';
import { ResultPreview } from '../../components/common/ResultPreview';

export function EmailPreviewPage() {
  const { workspace } = useWorkspace();
  return <div className="page-stack">
    <PageHeader title="Email Results Preview" description="Review Email mapping outcomes and download each result group." />
    <ActionLink to="/email_mapping_page">Back to Email mapping</ActionLink>
    {Object.keys(workspace.exports.email).length
      ? <ResultPreview key={workspace.workspace_id} stage="email" label="Email result group" />
      : <Alert>No Email results are available in this session. Run Email mapping first.</Alert>}
  </div>;
}
