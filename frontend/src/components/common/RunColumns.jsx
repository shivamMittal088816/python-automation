import { useWorkspace } from '../../context/WorkspaceContext';

export function RunColumns({ stage, pass }) {
  const { workspace } = useWorkspace();
  const columns = workspace.run_columns?.[stage]?.[pass];
  return <span className="font-normal break-words">({columns?.length ? `Last run: ${columns.join(' + ')}` : 'No saved run'})</span>;
}
