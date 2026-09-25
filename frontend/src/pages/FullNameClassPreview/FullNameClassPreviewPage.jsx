import { PageHeader } from '../../components/common/Presentation';
import { useWorkspace } from '../../context/WorkspaceContext';
import { ActionLink, Alert } from '../../components/common/Controls';
import { ResultPreview } from '../../components/common/ResultPreview';

export function FullNameClassPreviewPage() {
  const { workspace } = useWorkspace();
  return <div className="page-stack">
    <PageHeader title="Class Concatenation Results Preview" description="Review full-name and class-number matching outcomes and download each result group." />
    <ActionLink to="/full_name_class_mapping_page">Back to Class concatenation mapping</ActionLink>
    <p className="caption">Blank admission numbers are allowed. One match: Matched · Multiple matches or duplicate username/user ID: Review · No match: Not matched.</p>
    {Object.keys(workspace.exports.full_name_class).length
      ? <ResultPreview key={workspace.workspace_id} stage="full_name_class" label="Result group" />
      : <Alert>No Class concatenation results are available in this session. Run Class concatenation mapping first.</Alert>}
  </div>;
}
