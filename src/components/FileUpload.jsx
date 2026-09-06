import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, AlertCircle } from 'lucide-react';

export default function FileUpload({ onFileSelected, isLoading, error }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndPassFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndPassFile(e.target.files[0]);
    }
  };

  const validateAndPassFile = (file) => {
    const validExtensions = ['.csv', '.xlsx', '.xls', '.tsv'];
    const name = file.name.toLowerCase();
    const isValid = validExtensions.some(ext => name.endsWith(ext));

    if (!isValid) {
      alert('Por favor sube un archivo CSV o Excel (.xlsx, .xls).');
      return;
    }
    onFileSelected(file);
  };

  return (
    <div style={{ maxWidth: '820px', margin: '3rem auto', textAlign: 'center' }}>
      {/* Title */}
      <div style={{ marginBottom: '2.5rem' }}>
        <h2 style={{ fontSize: '2.2rem', fontWeight: 700, marginBottom: '0.6rem', color: 'var(--text-primary)' }}>
          Limpieza y Depuración de Datasets
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '560px', margin: '0 auto' }}>
          Sube un archivo en formato CSV o Excel para eliminar celdas vacías, filas repetidas,
          valores extremos y corregir errores tipográficos con <strong>Pandas</strong>.
        </p>
      </div>

      {/* Dropzone */}
      <div
        className={`dropzone ${isDragging ? 'active' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isLoading && fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInput}
          accept=".csv,.xlsx,.xls,.tsv"
          style={{ display: 'none' }}
        />

        <div className="dropzone-icon-box">
          {isLoading ? (
            <FileSpreadsheet size={32} />
          ) : (
            <UploadCloud size={32} />
          )}
        </div>

        {isLoading ? (
          <div>
            <h3 style={{ fontSize: '1.15rem', marginBottom: '0.35rem' }}>Procesando y limpiando dataset...</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Eliminando celdas faltantes, duplicados, outliers y corrigiendo tipografías con Pandas.
            </p>
          </div>
        ) : (
          <div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.35rem', fontWeight: 600 }}>
              Arrastra tu archivo aquí o haz clic para examinar
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem', marginBottom: '1.25rem' }}>
              Soporta archivos CSV y Excel (.xlsx, .xls)
            </p>

            <button
              type="button"
              className="btn btn-primary"
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
            >
              Seleccionar Dataset
            </button>
          </div>
        )}
      </div>

      {/* Error alert */}
      {error && (
        <div style={{
          marginTop: '1.25rem',
          padding: '0.85rem 1rem',
          borderRadius: 'var(--radius-sm)',
          background: '#1a1a1a',
          border: '1px solid #404040',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          gap: '0.65rem',
          textAlign: 'left',
          fontSize: '0.88rem'
        }}>
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
