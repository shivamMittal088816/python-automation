import { PageHeader } from '../../components/common/Presentation';
import { useWorkspace } from '../../context/WorkspaceContext';
import { ActionLink, Alert } from '../../components/common/Controls';
import { ResultPreview } from '../../components/common/ResultPreview';
export function AdmissionPreviewPage() {
  const { workspace } = useWorkspace();
  return <div className="page-stack"><PageHeader title="Admission Results Preview" description="Review mapping outcomes and download the records in each result group." /><div className="flex flex-wrap items-center gap-4"><ActionLink to="/dump_file_page">Search dump</ActionLink><ActionLink to="/admission_file_page">Back to mapping</ActionLink></div>{Object.keys(workspace.exports.admission).length ? <>{workspace.email_ready && <ActionLink primary to="/email_mapping_page">Email mapping for Not matched students</ActionLink>}<ResultPreview key={workspace.workspace_id} stage="admission" /></> : <Alert>No results available in this session. Map your files first to preview the results.</Alert>}</div>;
}
