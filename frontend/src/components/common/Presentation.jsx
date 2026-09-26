import { Link, useLocation } from 'react-router';

export function Icon({ name = 'file', className = 'size-5' }) {
  const paths = {
    file: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M8 13h8 M8 17h5',
    check: 'm5 12 4 4L19 6',
    upload: 'M12 16V3 m-5 5 5-5 5 5 M4 16v4h16v-4',
    download: 'M12 3v13 m-5-5 5 5 5-5 M4 20h16',
    mail: 'M3 5h18v14H3z m0 0 9 7 9-7',
    grid: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
    info: 'M12 11v6 M12 7h.01 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
  };
  return <svg aria-hidden="true" className={`shrink-0 ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name] || paths.file} /></svg>;
}

export function PageHeader({ title, description, showHelp = true }) {
  const { search } = useLocation();
  return <header className="border-b border-slate-200 pb-5"><p className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">Student operations</p><div className="flex items-center justify-between gap-3"><h2 className="text-2xl font-semibold tracking-tight text-slate-950">{title}</h2>{showHelp && <div className="group relative shrink-0">
    <Link to={`/mapping_rules_page${search}`} aria-label="Mapping rules / Help" title="Mapping rules / Help" className="flex size-9 items-center justify-center rounded-full border border-blue-200 bg-blue-50 text-base font-semibold text-blue-700 transition-colors hover:bg-blue-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600">?</Link>
    <span aria-hidden="true" className="pointer-events-none absolute right-0 top-full z-10 mt-2 whitespace-nowrap rounded-md bg-slate-900 px-3 py-2 text-xs font-medium text-white opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">Mapping rules / Help</span>
  </div>}</div><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{description}</p></header>;
}

export function SectionHeader({ title, description, step }) {
  return <div className="mb-4 flex items-start gap-3">{step && <span className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-blue-100 bg-blue-50 text-xs font-semibold text-blue-700">{step}</span>}<div><h3 className="font-semibold text-slate-900">{title}</h3>{description && <p className="mt-1 text-sm leading-5 text-slate-500">{description}</p>}</div></div>;
}

export function Stepper({ active = 0, labels = ['Add files', 'Configure mapping', 'Review results'] }) {
  return <ol aria-label="Mapping progress" className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-3">{labels.map((label, index) => <li key={label} aria-current={index === active ? 'step' : undefined} className={`flex items-center gap-3 rounded-lg px-3 py-2 ${index === active ? 'bg-blue-50' : ''}`}><span className={`flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${index < active ? 'bg-emerald-100 text-emerald-700' : index === active ? 'bg-blue-700 text-white' : 'bg-slate-100 text-slate-500'}`}>{index < active ? <Icon name="check" className="size-4" /> : `0${index + 1}`}</span><div><p className={`text-sm font-medium ${index === active ? 'text-blue-900' : 'text-slate-700'}`}>{label}</p><p className="mt-0.5 text-xs text-slate-500">{index < active ? 'Completed' : index === active ? 'Current step' : 'Upcoming'}</p></div></li>)}</ol>;
}

export function LoadedFile({ name }) {
  return <div className="flex min-w-0 items-start gap-3 rounded-lg border border-emerald-200 bg-emerald-50/60 px-3 py-3 text-sm"><span className="mt-0.5 text-emerald-700"><Icon name="check" className="size-4" /></span><p className="min-w-0 break-all font-medium text-slate-700">Loaded: {name}</p></div>;
}

export function EmptyState({ title, children }) {
  return <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-10 text-center"><span className="mx-auto mb-3 flex size-11 items-center justify-center rounded-xl bg-slate-100 text-slate-500"><Icon /></span><h3 className="font-semibold text-slate-800">{title}</h3><div className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">{children}</div></div>;
}

export function Badge({ children }) {
  const tone = children === 'Matched' || children === 'Completed' ? 'bg-emerald-50 text-emerald-800 ring-emerald-200' : children === 'Review' ? 'bg-amber-50 text-amber-800 ring-amber-200' : children === 'Not matched' || children === 'Failed' ? 'bg-red-50 text-red-800 ring-red-200' : 'bg-slate-100 text-slate-600 ring-slate-200';
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${tone}`}>{children}</span>;
}
