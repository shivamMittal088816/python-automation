import { useWorkspace } from '../../context/WorkspaceContext';
import { fileApi } from '../../services/fileApi';
import { ConfirmClearFile } from './ConfirmClearFile';

export function ClearMappingFileButton({ kind }) {
  const { workspace, busy, run } = useWorkspace();
  if (!workspace.files[kind]) return null;
  const label = kind === 'school' ? 'school' : kind === 'email_dump' ? 'email dump' : 'dump';
  return <ConfirmClearFile file={workspace.files[kind]} disabled={!!busy}
    label={`Clear ${label} file`} className="rounded-lg px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100 disabled:opacity-50"
    onConfirm={() => run('Clearing file...', revision => fileApi.clear(kind, revision))} />;
}
