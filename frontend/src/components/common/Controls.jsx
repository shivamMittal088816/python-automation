import { cloneElement, useId, useState } from 'react';
import { Badge, Icon } from './Presentation';
import { Link } from 'react-router';

export function ActionLink({ children, primary = false, ...props }) {
  return <Link className={`inline-flex min-h-10 max-w-full items-center justify-center gap-2 rounded-lg border px-4 py-2 text-sm font-semibold shadow-sm transition-colors ${primary ? 'border-blue-700 bg-blue-700 text-white hover:bg-blue-800' : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'}`} {...props}>{children}</Link>;
}

export function Button({ children, primary = false, variant, className = '', ...props }) {
  const styles = { primary: 'border-blue-700 bg-blue-700 text-white shadow-sm hover:border-blue-800 hover:bg-blue-800', secondary: 'border-slate-300 bg-white text-slate-700 shadow-sm hover:bg-slate-50', ghost: 'border-transparent text-slate-600 hover:bg-slate-100', danger: 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100' };
  return <button type="button" className={`inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-lg border px-4 py-2 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant || (primary ? 'primary' : 'secondary')]} ${className}`} {...props}>{children}</button>;
}
export function Alert({ type = 'info', children }) {
  const colors = { info: 'border-blue-200 bg-blue-50 text-blue-900', warning: 'border-amber-300 bg-amber-50 text-amber-900', error: 'border-red-200 bg-red-50 text-red-900', success: 'border-green-200 bg-green-50 text-green-900' };
  return <div role={type === 'error' ? 'alert' : 'status'} className={`my-3 flex items-start gap-3 rounded-lg border px-4 py-3 text-sm leading-6 ${colors[type] || colors.info}`}><Icon name={type === 'success' ? 'check' : 'info'} className="mt-0.5 size-4" /><div className="min-w-0 break-words">{children}</div></div>;
}
export function Field({ label, children }) {
  const generatedId = useId(), id = children.props.id || generatedId;
  return <div className="flex min-w-0 flex-col gap-2 text-sm font-medium text-slate-700"><label htmlFor={id}>{label}</label>{cloneElement(children, { id })}</div>;
}
export function Select({ label, options, ...props }) {
  return <Field label={label}><select className="input" {...props}>{options.map(option => {
    const item = typeof option === 'object' && option !== null ? option : { value: option ?? '', label: option ?? 'Choose a column' };
    return <option key={String(item.value)} value={item.value}>{item.label}</option>;
  })}</select></Field>;
}
export function Input({ label, ...props }) { return <Field label={label}><input className="input" {...props} /></Field>; }
export function Card({ children, className = '' }) { return <section className={`min-w-0 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5 ${className}`}>{children}</section>; }
export function Metrics({ items }) {
  const tones = { Matched: 'border-t-emerald-500', Review: 'border-t-amber-500', 'Not matched': 'border-t-rose-400' };
  return <div className={`grid grid-cols-1 gap-3 sm:grid-cols-2 ${items.length === 3 ? 'lg:grid-cols-3' : items.length > 3 ? 'lg:grid-cols-4' : ''}`}>{items.map(([label, value]) => <div key={label} className={`min-w-0 rounded-xl border border-t-2 border-slate-200 bg-white p-4 ${tones[label] || 'border-t-blue-400'}`}><div className="text-xs font-medium text-slate-600">{tones[label] ? <Badge>{label}</Badge> : label}</div><div className="mt-2 break-words text-2xl font-semibold tracking-tight text-slate-900 tabular-nums">{typeof value === 'number' ? value.toLocaleString() : value ?? '—'}</div></div>)}</div>;
}
export function Loading({ children = 'Loading…' }) { return <div role="status" className="flex items-center gap-3 rounded-lg bg-slate-100 px-4 py-3 text-sm text-slate-600"><span aria-hidden="true" className="size-4 shrink-0 animate-spin rounded-full border-2 border-slate-300 border-t-blue-700 motion-reduce:animate-none" />{children}</div>; }
export function DownloadButton({ action, children }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function download() { setBusy(true); setError(''); try { await action(); } catch (error) { setError(error.message); } finally { setBusy(false); } }
  return <div><Button disabled={busy} onClick={download}>{busy ? 'Preparing download…' : children}</Button>{error && <Alert type="error">{error}</Alert>}</div>;
}
