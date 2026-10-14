import { useState } from 'react';
import './page-pdf-download.css';

export function PagePdfDownload({ targetRef, filename, label = 'Download page PDF' }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function download() {
    const target = targetRef.current;
    if (!target || busy) return;
    setBusy(true);
    setError('');
    try {
      const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
        import('html2canvas'), import('jspdf'),
      ]);
      const canvas = await html2canvas(target, {
        backgroundColor: '#ffffff',
        scale: Math.min(1.5, window.devicePixelRatio || 1),
        useCORS: true,
        logging: false,
        ignoreElements: element => element.hasAttribute('data-pdf-exclude'),
        windowWidth: Math.max(target.scrollWidth, 1100),
      });
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 10;
      const imageWidth = pageWidth - margin * 2;
      const imageHeight = canvas.height * imageWidth / canvas.width;
      const image = canvas.toDataURL('image/jpeg', 0.92);
      let offset = 0;
      let page = 0;
      while (offset < imageHeight) {
        if (page > 0) pdf.addPage();
        pdf.addImage(image, 'JPEG', margin, margin - offset, imageWidth, imageHeight);
        offset += pageHeight - margin * 2;
        page += 1;
      }
      pdf.save(filename);
    } catch (downloadError) {
      setError(downloadError?.message || 'Could not create the PDF.');
    } finally {
      setBusy(false);
    }
  }

  return <div className="page-pdf-control" data-pdf-exclude>
    <button className="page-pdf-button" type="button" disabled={busy} onClick={download}>
      <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3v12m0 0 4-4m-4 4-4-4M5 19h14" /></svg>
      {busy ? 'Creating PDF…' : label}
    </button>
    {error && <span role="alert">{error}</span>}
  </div>;
}
