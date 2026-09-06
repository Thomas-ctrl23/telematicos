import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import MetricsSummary from './components/MetricsSummary';
import DataTable from './components/DataTable';
import ExportBar from './components/ExportBar';
import { Sparkles, Eye, RotateCcw } from 'lucide-react';

const CLEANING_CONFIG = {
  missing: {
    enabled: true,
    mode: 'drop_rows_any',
    threshold_pct: 50,
    drop_empty_columns: false,
  },
  duplicates: {
    enabled: true,
    subset: null,
    keep: 'first',
  },
  outliers: {
    enabled: true,
    method: 'iqr',
    action: 'remove',
    factor: 1.5,
    columns: null,
  },
  typos: {
    enabled: true,
    normalize_whitespace: true,
    normalize_casing: false,
    fuzzy_unify: true,
    similarity_threshold: 0.85,
    columns: null,
  },
};

export default function App() {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [inspection, setInspection] = useState(null);
  const [cleanResults, setCleanResults] = useState(null);
  const [activeTableView, setActiveTableView] = useState('cleaned');

  const handleFileSelected = async (selectedFile) => {
    try {
      setFile(selectedFile);
      setIsLoading(true);
      setError(null);
      setCleanResults(null);
      setInspection(null);

      // 1. Analizar dataset
      const formDataAnalyze = new FormData();
      formDataAnalyze.append('file', selectedFile);

      const responseAnalyze = await fetch('/api/analyze', {
        method: 'POST',
        body: formDataAnalyze,
      });

      if (!responseAnalyze.ok) {
        const errJson = await responseAnalyze.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Error al analizar el dataset.');
      }

      const inspectionData = await responseAnalyze.json();
      setInspection(inspectionData);

      // 2. Ejecutar limpieza automática con Pandas
      const formDataClean = new FormData();
      formDataClean.append('file', selectedFile);
      formDataClean.append('config', JSON.stringify(CLEANING_CONFIG));

      const responseClean = await fetch('/api/clean', {
        method: 'POST',
        body: formDataClean,
      });

      if (!responseClean.ok) {
        const errJson = await responseClean.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Error durante el proceso de limpieza.');
      }

      const cleanData = await responseClean.json();
      setCleanResults(cleanData);
      setActiveTableView('cleaned');
    } catch (err) {
      console.error(err);
      setError(err.message);
      setFile(null);
      setInspection(null);
      setCleanResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setInspection(null);
    setCleanResults(null);
    setError(null);
  };

  return (
    <div className="app-container">
      {/* Top Bar when dataset is active */}
      {inspection && (
        <div className="stepper-nav">
          <div className="stepper-steps">
            <div className="step-item completed">
              <div className="step-number">✓</div>
              <span>{file?.name}</span>
            </div>
            <div className="step-item completed">
              <div className="step-number">✓</div>
              <span>Limpieza con Pandas completada</span>
            </div>
          </div>

          <button
            onClick={handleReset}
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
          >
            <RotateCcw size={13} />
            <span>Cargar otro archivo</span>
          </button>
        </div>
      )}

      {/* UPLOAD SCREEN */}
      {!inspection && (
        <FileUpload
          onFileSelected={handleFileSelected}
          isLoading={isLoading}
          error={error}
        />
      )}

      {/* RESULTS SCREEN */}
      {inspection && cleanResults && (
        <>
          {/* Metrics summary */}
          <MetricsSummary
            initialInspection={inspection}
            cleanResults={cleanResults}
          />

          {/* Export bar (Download CSV / Excel) */}
          <ExportBar
            file={file}
            config={CLEANING_CONFIG}
            cleanResults={cleanResults}
          />

          {/* Table Preview Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button
                className={`btn ${activeTableView === 'cleaned' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '0.4rem 0.85rem' }}
                onClick={() => setActiveTableView('cleaned')}
              >
                <Sparkles size={14} />
                <span>Dataset Limpio ({cleanResults.metrics.final_rows} filas)</span>
              </button>

              <button
                className={`btn ${activeTableView === 'original' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.82rem', padding: '0.4rem 0.85rem' }}
                onClick={() => setActiveTableView('original')}
              >
                <Eye size={14} />
                <span>Dataset Original ({inspection.total_rows} filas)</span>
              </button>
            </div>

            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {activeTableView === 'cleaned'
                ? 'Datos tras eliminar nulos, duplicados, outliers y corregir tipografías'
                : 'Estructura original sin procesar'}
            </span>
          </div>

          {/* Data Table */}
          {activeTableView === 'cleaned' ? (
            <DataTable
              title="Previsualización: Datos Limpios"
              data={cleanResults.preview}
              columns={cleanResults.columns}
              isCleaned={true}
            />
          ) : (
            <DataTable
              title="Previsualización: Datos Originales"
              data={inspection.preview}
              columns={inspection.columns}
              isCleaned={false}
            />
          )}
        </>
      )}
    </div>
  );
}
