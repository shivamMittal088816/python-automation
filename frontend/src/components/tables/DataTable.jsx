export function DataTable({ rows = [], columns = rows[0] ? Object.keys(rows[0]) : [], labels = {}, offset = 0, highlight = '', scope = null }) {
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
  return <div className="max-h-[520px] overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm" role="region" aria-label="Student records" tabIndex={0}><table className="w-full border-collapse text-left text-sm"><thead className="sticky top-0 z-10 bg-slate-100 text-xs font-semibold text-slate-600"><tr>{columns.map(column => <th scope="col" className="whitespace-nowrap border-b border-slate-200 px-4 py-3" key={column}>{labels[column] || column}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={offset + index} className="odd:bg-white even:bg-slate-50/60 hover:bg-blue-50">{columns.map(column => <td className={`whitespace-pre border-b border-slate-100 px-4 py-2.5 text-slate-700 ${typeof row[column] === 'number' ? 'font-medium tabular-nums' : ''}`} key={column}>{cell(row[column], column)}</td>)}</tr>)}</tbody></table></div>;
}
