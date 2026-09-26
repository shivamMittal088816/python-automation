import { useEffect, useState } from 'react';
import { ClearMappingFileButton } from './ClearMappingFileButton';
import { useWorkspace } from '../../context/WorkspaceContext';
import { fileApi } from '../../services/fileApi';
import { Button, Input } from './Controls';
import { Icon, LoadedFile } from './Presentation';

export function FileInput({ kind, label }) {
  const { workspace, busy, run } = useWorkspace();
  const [tab, setTab] = useState('Upload');
  const [path, setPath] = useState(workspace.files[kind]?.path || '');
  useEffect(() => {
    if (!workspace.files[kind]) setPath('');
  }, [workspace.files[kind]]);

  const loadUpload = event => {
    const file = event.target.files[0];
    event.target.value = '';
    if (file) run('Loading file…', revision => fileApi.upload(kind, file, revision));
  };

  const loadPath = event => {
    event.preventDefault();
    run('Loading file…', revision => fileApi.path(kind, path, revision));
  };

  return <div className="space-y-3" data-testid={`${kind}-input`}>
    <div role="tablist" aria-label={`${label} file source`} className="inline-flex rounded-lg bg-slate-100 p-1">
      {['Upload', 'File path'].map(name => <button type="button" role="tab" aria-selected={tab === name} key={name} onClick={() => setTab(name)} className={`min-h-9 rounded-md px-5 py-1.5 text-sm font-medium transition-colors ${tab === name ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-500 hover:text-slate-900'}`}>{name}</button>)}
    </div>
    {tab === 'Upload' ? <label className={`relative flex flex-col items-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50/70 px-4 py-7 text-center transition-colors focus-within:border-blue-600 focus-within:ring-2 focus-within:ring-blue-100 ${busy ? 'opacity-50' : 'hover:border-blue-400 hover:bg-blue-50/40'}`}>
      <span className="mb-3 rounded-lg bg-white p-2.5 text-blue-700 shadow-sm"><Icon name="upload" /></span>
      <span className="text-sm font-semibold text-slate-800">Add {label} file</span>
      <span aria-hidden="true" className="mt-1 text-sm text-slate-500">Click to browse your files</span>
      <span aria-hidden="true" className="mt-3 text-xs text-slate-400">CSV or XLSX · Maximum file size 100 MB</span>
      <input aria-label={`Add ${label} file`} disabled={!!busy} type="file" accept=".csv,.xlsx" className="absolute inset-0 h-full w-full cursor-pointer opacity-0 disabled:cursor-not-allowed" onChange={loadUpload} />
    </label> : <form className="space-y-3" onSubmit={loadPath}>
      <Input label="File path" value={path} onChange={event => setPath(event.target.value)} placeholder="C:\Users\USER\Downloads\students.xlsx" />
      <p className="text-xs leading-5 text-slate-500">Use a path on the computer running the backend. Load it again to read changes on disk.</p>
      <Button type="submit" disabled={!!busy}>Use file path</Button>
    </form>}
    {workspace.files[kind] ? <div className="flex flex-wrap items-center justify-between gap-2"><LoadedFile name={workspace.files[kind].name} /><ClearMappingFileButton kind={kind} /></div> : <p className="text-xs text-slate-500">No file selected · CSV or XLSX</p>}
  </div>;
}
