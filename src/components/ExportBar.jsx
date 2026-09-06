import React, { useState } from 'react';
import { Download, FileSpreadsheet, FileText, CheckCircle2 } from 'lucide-react';

export default function ExportBar({ file, config, cleanResults }) {
  const [downloading, setDownloading] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const handleDownload = async (format) => {
    if (!file) return;

    try {
      setDownloading(true);
      setDownloadSuccess(false);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('config', JSON.stringify(config));
      formData.append('export_format', format);

      const response = await fetch('/api/export', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Error al descargar el archivo limpio.');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      const extension = format === 'excel' ? 'xlsx' : 'csv';
      const baseName = file.name.replace(/\.[^/.]+$/, "");
      a.download = `${baseName}_limpio.${extension}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 4000);
    } catch (err) {
      console.error(err);
      alert('Error descargando el archivo: ' + err.message);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div
      className="glass-card"
      style={{
        padding: '1.25rem 1.5rem',
        marginBottom: '2.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1.25rem',
      }}
    >
      <div>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.2rem' }}>
          Exportar Dataset Limpio
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: 0 }}>
          Descarga el archivo procesado libre de filas repetidas, celdas vacías y outliers tratados.
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        {downloadSuccess && (
          <span className="badge" style={{ padding: '0.45rem 0.75rem' }}>
            <CheckCircle2 size={13} /> ¡Descarga iniciada!
          </span>
        )}

        <button
          onClick={() => handleDownload('csv')}
          disabled={downloading}
          className="btn btn-secondary"
        >
          <FileText size={15} />
          <span>Descargar CSV</span>
        </button>

        <button
          onClick={() => handleDownload('excel')}
          disabled={downloading}
          className="btn btn-primary"
        >
          <FileSpreadsheet size={15} />
          <span>Descargar Excel (.xlsx)</span>
        </button>
      </div>
    </div>
  );
}
