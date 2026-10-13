import { DataTable } from '../../components/tables/DataTable';

export function RollbackDumpPreview({ dump, school, busy, onPage, onDownload }) {
  if (!dump || !school) return null;
  const page = dump.page || 1;
  const pageSize = dump.page_size || 20;
  const totalPages = dump.total_pages || 1;
  return <details open className="bulk-card bulk-input-preview rollback-preview">
    <summary>Database dump preview <span>School {school.school_index}</span></summary>
    <div className="rollback-dump-actions">
      <button className="bulk-button bulk-secondary" disabled={!!busy} onClick={() => onDownload('xlsx')}>Download Excel</button>
      <button className="bulk-button bulk-secondary" disabled={!!busy} onClick={() => onDownload('csv')}>Download CSV</button>
    </div>
    <p className="bulk-hint">Showing {dump.rows.length} of {dump.row_count.toLocaleString()} matching student records.</p>
    {dump.rows.length
      ? <DataTable variant="preview" rows={dump.rows} columns={dump.columns} ariaLabel="Rollback database dump records" />
      : <p className="bulk-hint" role="status">No matching student records were found for this school.</p>}
    {totalPages > 1 && <nav className="bulk-pagination" aria-label="Rollback database dump preview pages">
      <span>Rows {(page - 1) * pageSize + 1}&ndash;{Math.min(page * pageSize, dump.row_count)} of {dump.row_count}</span>
      <div className="bulk-pagination-controls">
        <button className="bulk-button bulk-secondary" disabled={!!busy || page <= 1} onClick={() => onPage(page - 1)}>Previous</button>
        <span>Page {page} of {totalPages}</span>
        <button className="bulk-button bulk-secondary" disabled={!!busy || page >= totalPages} onClick={() => onPage(page + 1)}>Next</button>
      </div>
    </nav>}
  </details>;
}
