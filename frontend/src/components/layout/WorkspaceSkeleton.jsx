import { Icon } from '../common/Presentation';

function Placeholder({ className = '' }) {
  return <div className={`workspace-placeholder rounded-md bg-slate-200/70 ${className}`} />;
}

export function WorkspaceSkeleton() {
  return <div role="status" aria-label="Loading workspace" aria-busy="true">
    <span className="sr-only">Loading your mapping workspace…</span>
    <div aria-hidden="true" className="min-h-screen bg-slate-50 text-slate-900">
      <header className="flex h-16 items-center border-b border-slate-200 bg-white px-4 sm:px-6 lg:px-8">
        <span className="flex size-10 items-center justify-center rounded-lg border border-slate-200 text-slate-400"><Icon name="menu" /></span>
      </header>
      <main className="min-w-0 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <div className="w-full space-y-4">
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
