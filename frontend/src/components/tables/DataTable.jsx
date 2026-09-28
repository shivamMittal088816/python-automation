export function DataTable({
  rows = [], columns: suppliedColumns, labels = {}, offset = 0,
  highlight = '', scope = null, variant = 'default', ariaLabel = 'Student records',
}) {
  const columns = suppliedColumns || (rows[0] && !Array.isArray(rows[0]) ? Object.keys(rows[0]) : []);
  const preview = variant === 'preview';
  const needle = highlight.trim().toLowerCase();
  function cell(value, column) {
    const text = value == null ? '' : typeof value === 'object' ? JSON.stringify(value) : String(value);
    if (!needle || scope && !scope.includes(column)) return text;
    const searchable = text.toLowerCase();
    const parts = []; let previous = 0, index;
    while ((index = searchable.indexOf(needle, previous)) !== -1) {
      parts.push(text.slice(previous, index), <mark className="rounded bg-amber-200 text-amber-950" key={index}>{text.slice(index, index + needle.length)}</mark>);
      previous = index + needle.length;
    }
    parts.push(text.slice(previous)); return parts;
  }
  const valueAt = (row, column, columnIndex) => Array.isArray(row) ? row[columnIndex] : row[column];
  const containerClass = preview
    ? 'mt-3 max-h-[360px] overflow-auto rounded-lg border border-slate-200 bg-white'
    : 'max-h-[520px] overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm';
  const tableClass = preview
    ? 'w-full border-collapse text-left text-xs'
    : 'w-full border-collapse text-left text-sm';
  const headerClass = preview
    ? 'sticky top-0 z-10 bg-[#f0f5f6] text-xs font-semibold text-[#44616b]'
    : 'sticky top-0 z-10 bg-slate-100 text-xs font-semibold text-slate-600';
  const headingClass = preview
    ? 'whitespace-nowrap border-b border-slate-200 px-3 py-2.5'
    : 'whitespace-nowrap border-b border-slate-200 px-4 py-3';
  const rowClass = preview
    ? 'odd:bg-white even:bg-slate-50/80 hover:bg-teal-50/60'
    : 'odd:bg-white even:bg-slate-50/60 hover:bg-blue-50';
  const cellClass = preview
    ? 'whitespace-pre border-b border-slate-100 px-3 py-2.5 text-slate-700'
    : 'whitespace-pre border-b border-slate-100 px-4 py-2.5 text-slate-700';

  return <div className={containerClass} role="region" aria-label={ariaLabel} tabIndex={0}>
    <table className={tableClass}>
      <thead className={headerClass}><tr>{columns.map((column, columnIndex) => <th scope="col" className={headingClass} key={`${column}-${columnIndex}`}>{labels[column] || column}</th>)}</tr></thead>
      <tbody>{rows.map((row, index) => <tr key={offset + index} className={rowClass}>{columns.map((column, columnIndex) => {
        const value = valueAt(row, column, columnIndex);
        return <td className={`${cellClass} ${typeof value === 'number' ? 'font-medium tabular-nums' : ''}`} key={`${column}-${columnIndex}`}>{cell(value, column)}</td>;
      })}</tr>)}</tbody>
    </table>
  </div>;
}
