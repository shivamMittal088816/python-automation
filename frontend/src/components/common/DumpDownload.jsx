import { useState } from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { fileApi } from '../../services/fileApi';
import { DownloadButton, Select } from './Controls';
export function DumpDownload({ kind = 'dump' }) {
  const { id, workspace } = useWorkspace(), saved = workspace.files[kind];
  const [format, setFormat] = useState('csv'), [sheet, setSheet] = useState(saved?.sheets?.[0] || '');
  if (!saved) return null;
  return <div className="flex flex-wrap items-end gap-3"><Select label="Download format" options={[{ value: 'csv', label: 'CSV' }, { value: 'xlsx', label: 'XLSX' }]} value={format} onChange={event => setFormat(event.target.value)} />{format === 'csv' && saved.sheets.length > 1 && <Select label="Sheet to download" options={saved.sheets} value={sheet} onChange={event => setSheet(event.target.value)} />}<DownloadButton action={() => fileApi.download(kind, { format, sheet: sheet || undefined })}>Download dump file</DownloadButton></div>;
}
