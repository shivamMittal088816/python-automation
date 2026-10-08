import { ClearMappingFileButton } from './ClearMappingFileButton';
import { useWorkspace } from '../../context/WorkspaceContext';
import { fileApi } from '../../services/fileApi';
import { Icon } from './Presentation';

export function FileInput({ kind, label }) {
  const { workspace, busy, run } = useWorkspace();
  const savedFile = workspace.files[kind];

  const loadUpload = event => {
    const file = event.target.files[0];
    event.target.value = '';
    if (file) run('Loading file…', revision => fileApi.upload(kind, file, revision, workspace.operation_scope));
  };

  return <div className="mapping-file-input space-y-3" data-testid={`${kind}-input`}>
    {savedFile ? <div className={`flex flex-col items-center rounded-xl border-2 border-solid border-emerald-300 bg-emerald-50/70 px-4 py-4 text-center ${busy ? 'opacity-50' : ''}`}>
        <span className="mb-2 rounded-lg bg-white p-2 text-emerald-700 shadow-sm"><Icon name="check" className="size-4" /></span>
        <span role="status" className="text-sm font-semibold text-emerald-800">File uploaded successfully</span>
        <span className="mt-0.5 max-w-full break-all text-sm font-medium text-slate-700">{savedFile.name}</span>
        <div className="mt-3 flex flex-wrap items-center justify-center gap-1.5">
          <label className={`mapping-replace-file relative inline-flex min-h-8 cursor-pointer items-center justify-center rounded-lg border border-emerald-300 bg-white px-3 py-1 text-xs font-semibold text-emerald-800 shadow-sm transition-colors hover:bg-emerald-50 ${busy ? 'cursor-not-allowed opacity-50' : ''}`}>
            Replace
            <input aria-label={`Replace ${label} file`} disabled={!!busy} type="file" accept=".csv,.xlsx" className="absolute inset-0 h-full w-full cursor-pointer opacity-0 disabled:cursor-not-allowed" onChange={loadUpload} />
          </label>
          <ClearMappingFileButton kind={kind} className="min-h-8 rounded-lg px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-emerald-100 disabled:opacity-50" />
        </div>
      </div> : <label className={`relative flex flex-col items-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50/70 px-4 py-7 text-center transition-colors focus-within:border-blue-600 focus-within:ring-2 focus-within:ring-blue-100 ${busy ? 'opacity-50' : 'hover:border-blue-400 hover:bg-blue-50/40'}`}>
        <span className="mb-3 rounded-lg bg-white p-2.5 text-blue-700 shadow-sm"><Icon name="upload" /></span>
        <span className="text-sm font-semibold text-slate-800">Add {label} file</span>
        <span aria-hidden="true" className="mt-1 text-sm text-slate-500">Click to browse your files</span>
        <span aria-hidden="true" className="mt-3 text-xs text-slate-400">CSV or XLSX · Maximum file size 100 MB</span>
        <input aria-label={`Add ${label} file`} disabled={!!busy} type="file" accept=".csv,.xlsx" className="absolute inset-0 h-full w-full cursor-pointer opacity-0 disabled:cursor-not-allowed" onChange={loadUpload} />
    </label>}
    {!savedFile && <p className="text-xs text-slate-500">No file selected · CSV or XLSX</p>}
  </div>;
}
