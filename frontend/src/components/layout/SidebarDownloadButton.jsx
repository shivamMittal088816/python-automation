import { useState } from 'react';
import { Icon } from '../common/Presentation';
import { useWorkspace } from '../../context/WorkspaceContext';
import { fileApi } from '../../services/fileApi';

export function SidebarDownloadButton() {
  const { workspace } = useWorkspace();
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');
  const ready = Object.values(workspace.exports).some(stage => Object.keys(stage).length > 0);

  async function download() {
    setDownloading(true);
    setError('');
    try { await fileApi.download('final-results'); }
    catch (downloadError) { setError(downloadError.message); }
    finally { setDownloading(false); }
  }

  return <div>
    <button
      type="button"
      disabled={!ready || downloading}
      title={ready ? 'Download available mapping result groups' : 'Run at least one mapping to enable this download'}
      onClick={download}
      className="flex w-full items-center gap-3 rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-left text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400 disabled:shadow-none"
    >
      <Icon name="download" className="size-4" />
      <span className="min-w-0 flex-1">{downloading ? 'Preparing results…' : 'Download mapping results'}</span>
    </button>
    {error && <p role="alert" className="mt-2 text-xs leading-5 text-red-700">{error}</p>}
  </div>;
}
