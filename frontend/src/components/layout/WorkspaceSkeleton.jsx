import { Icon } from '../common/Presentation';

function Placeholder({ className = '' }) {
  return <div className={`workspace-placeholder rounded-md bg-slate-200/70 ${className}`} />;
}

export function WorkspaceSkeleton() {
  return <div role="status" aria-label="Loading workspace" aria-busy="true">
    <span className="sr-only">Loading your mapping workspace…</span>
    <div aria-hidden="true" className="min-h-screen bg-slate-50 text-slate-900 md:flex">
      <aside className="border-b border-slate-200 bg-white p-4 md:fixed md:inset-y-0 md:w-64 md:overflow-y-auto md:border-r">
        <div className="mb-7 flex items-center gap-3 px-2">
          <span className="rounded-xl bg-blue-700 p-2.5 text-white"><Icon name="grid" /></span>
          <div><p className="text-sm font-bold tracking-tight">Student Mapping</p><p className="mt-0.5 text-xs text-slate-500">Operations workspace</p></div>
        </div>
        <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-400">Mapping</p>
        <div className="space-y-2">
          {['Admission No. Mapping', 'Email mapping', 'Full name + class Number'].map((name, index) => <div key={name} className="px-3 py-2.5">
            <p className="text-xs font-semibold text-slate-500">{name}</p>
            {index === 0 && <div className="mt-3 space-y-3 border-l border-slate-200 py-2 pl-5"><Placeholder className="h-8 w-full bg-blue-100/60" /><Placeholder className="h-4 w-3/4" /></div>}
          </div>)}
        </div>
        <p className="mb-2 mt-7 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-400">Data files</p>
        {['School file', 'Dump file'].map(name => <div key={name} className="flex items-center gap-3 px-3 py-2.5 text-sm text-slate-500"><Icon name="file" className="size-4" />{name}</div>)}
        <div className="mt-8 hidden space-y-3 border-t border-slate-100 px-3 pt-5 md:block"><Placeholder className="h-3 w-24" /><Placeholder className="h-3 w-full" /><Placeholder className="h-3 w-4/5" /></div>
      </aside>
      <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 md:ml-64 lg:px-8 lg:py-8">
        <div className="mx-auto max-w-7xl space-y-4">
          <div className="space-y-3 border-b border-l-[3px] border-slate-200 border-l-blue-600 pb-5 pl-4"><Placeholder className="h-3 w-32" /><Placeholder className="h-7 w-3/5 max-w-80" /><Placeholder className="h-4 w-4/5 max-w-xl" /></div>
          <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-3">{[0, 1, 2].map(step => <div key={step} className="flex items-center gap-3 px-3 py-2"><Placeholder className="size-8 shrink-0 rounded-full" /><div className="flex-1 space-y-2"><Placeholder className="h-3 w-4/5" /><Placeholder className="h-2 w-1/2" /></div></div>)}</div>
          <div className="grid items-start gap-4 lg:grid-cols-2">{[0, 1].map(card => <div key={card} className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
            <div className="mb-5 flex gap-3"><Placeholder className="size-8 shrink-0" /><div className="flex-1 space-y-2"><Placeholder className="h-4 w-32" /><Placeholder className="h-3 w-4/5" /></div></div>
            <Placeholder className="mb-4 h-10 w-full" />
            <div className="flex h-40 flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50"><Placeholder className="size-10" /><Placeholder className="h-3 w-36" /><Placeholder className="h-3 w-24" /></div>
            <Placeholder className="mt-4 h-3 w-36" />
          </div>)}</div>
        </div>
      </main>
    </div>
  </div>;
}
