import { useWorkspace } from '../../context/WorkspaceContext';

export function SchoolIdentity() {
  const saved = useWorkspace().workspace.files.dump;
  if (!saved?.school_index && !saved?.school_name) return null;
  return <section aria-label="Current school" className="school-identity mb-5 flex min-w-0 flex-wrap items-center gap-3 rounded-xl border border-teal-200 p-3 sm:gap-4 sm:px-4">
    <div className="shrink-0 rounded-lg border border-teal-600 bg-teal-700 px-4 py-2 text-white shadow-sm">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-teal-100">School index</p>
      <p className="text-xl font-bold leading-7 tabular-nums">{saved.school_index || 'Not set'}</p>
    </div>
    <div className="min-w-0 flex-1 basis-48">
      <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-teal-700">Current school</p>
      <p className="break-words text-base font-semibold leading-6 text-slate-900 sm:text-lg">{saved.school_name || 'School name not provided'}</p>
    </div>
  </section>;
}
