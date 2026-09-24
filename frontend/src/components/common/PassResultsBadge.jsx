import { useWorkspace } from '../../context/WorkspaceContext';

export function PassResultsBadge({ stage }) {
  const { workspace } = useWorkspace();
  if (!Object.keys(workspace.exports[stage] || {}).length) return null;
  const pass = stage === 'full_name_class' ? workspace.full_name_class_round : workspace[`${stage}_result_pass`];
  return <p role="status" className={`inline-flex max-w-full items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-semibold ${pass === 2 ? 'border-indigo-200 bg-indigo-50 text-indigo-800' : 'border-blue-200 bg-blue-50 text-blue-800'}`}>
    <span aria-hidden="true" className={`size-1.5 shrink-0 rounded-full ${pass === 2 ? 'bg-indigo-500' : 'bg-blue-500'}`} />
    {pass === 2 ? 'Showing pass 1 + pass 2 results' : 'Showing pass 1 results'}
  </p>;
}
