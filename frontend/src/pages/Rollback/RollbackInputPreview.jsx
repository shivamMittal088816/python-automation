import { useEffect, useState } from 'react';
import { DataTable } from '../../components/tables/DataTable';

export function RollbackInputPreview({ file, busy, onPage }) {
  if (!file) return null;
  const page = file.page || 1;
  const pageSize = file.page_size || 20;
  const totalPages = file.total_pages || 1;
  return <details open className="bulk-card bulk-input-preview rollback-preview">
    <summary>Input preview <span>{file.name}</span></summary>
    <p className="bulk-hint">Showing {file.rows.length} of {file.row_count.toLocaleString()} source records from {file.sheet || 'the CSV file'}.</p>
    <DataTable variant="preview" rows={file.rows} columns={file.columns} ariaLabel="Rollback input records" />
    {totalPages > 1 && <nav className="bulk-pagination" aria-label="Rollback input preview pages">
      <span>Rows {(page - 1) * pageSize + 1}&ndash;{Math.min(page * pageSize, file.row_count)} of {file.row_count}</span>
      <div className="bulk-pagination-controls">
        <button className="bulk-button bulk-secondary" disabled={!!busy || page <= 1} onClick={() => onPage(page - 1)}>Previous</button>
        <PreviewPageJump page={page} totalPages={totalPages} busy={busy} onGo={onPage} />
        <button className="bulk-button bulk-secondary" disabled={!!busy || page >= totalPages} onClick={() => onPage(page + 1)}>Next</button>
      </div>
    </nav>}
  </details>;
}

function PreviewPageJump({ page, totalPages, busy, onGo }) {
  const [value, setValue] = useState(String(page));
  useEffect(() => setValue(String(page)), [page]);
  const requested = Number(value);
  const valid = Number.isInteger(requested) && requested >= 1 && requested <= totalPages;

  function submit(event) {
    event.preventDefault();
    if (valid && requested !== page) onGo(requested);
  }

  return <form className="bulk-page-jump" onSubmit={submit}>
    <label htmlFor="rollback-preview-page">Page</label>
    <input id="rollback-preview-page" type="number" min="1" max={totalPages} step="1" value={value} disabled={!!busy} onChange={event => setValue(event.target.value)} aria-describedby="rollback-preview-pages" />
    <span id="rollback-preview-pages">of {totalPages}</span>
    <button className="bulk-button bulk-secondary" type="submit" disabled={!!busy || !valid || requested === page}>Go</button>
  </form>;
}
