import React from 'react';
import { Database, CheckCircle, Trash2, ShieldAlert } from 'lucide-react';

export default function MetricsSummary({ initialInspection, cleanResults }) {
  const isCleaned = !!cleanResults;

  const initialRows = isCleaned
    ? cleanResults.metrics.initial_rows
    : initialInspection?.total_rows || 0;

  const finalRows = isCleaned
    ? cleanResults.metrics.final_rows
    : initialInspection?.total_rows || 0;

  const rowsRemoved = isCleaned
    ? cleanResults.metrics.rows_removed
    : 0;

  const reductionPct = isCleaned
    ? cleanResults.metrics.reduction_percentage
    : 0;

  const missingCount = isCleaned
    ? cleanResults.metrics.remaining_missing_cells
    : initialInspection?.total_missing_cells || 0;

  const duplicateCount = isCleaned
    ? cleanResults.metrics.remaining_duplicate_rows
    : initialInspection?.duplicate_rows || 0;

  return (
    <div className="metrics-grid">
      {/* Total Registros / Filas Finales */}
      <div className="metric-card">
        <div className="metric-header">
          <span>{isCleaned ? 'Filas Limpias Finales' : 'Filas Totales'}</span>
          <div className="metric-icon">
            <Database size={16} />
          </div>
        </div>
        <div className="metric-value">
          {finalRows.toLocaleString()}
        </div>
        <div className="metric-subtext">
          {isCleaned ? (
            <span style={{ color: '#ffffff', fontWeight: 600 }}>
              Dataset depurado
            </span>
          ) : (
            `${initialInspection?.total_cols || 0} columnas detectadas`
          )}
        </div>
      </div>

      {/* Filas Eliminadas */}
      <div className="metric-card">
        <div className="metric-header">
          <span>Filas Eliminadas</span>
          <div className="metric-icon">
            <Trash2 size={16} />
          </div>
        </div>
        <div className="metric-value">
          {rowsRemoved.toLocaleString()}
        </div>
        <div className="metric-subtext">
          {isCleaned ? (
            <span>Reducción del {reductionPct}%</span>
          ) : (
            <span>Tras aplicar la limpieza</span>
          )}
        </div>
      </div>

      {/* Celdas Faltantes */}
      <div className="metric-card">
        <div className="metric-header">
          <span>Celdas Faltantes</span>
          <div className="metric-icon">
            <ShieldAlert size={16} />
          </div>
        </div>
        <div className="metric-value">
          {missingCount}
        </div>
        <div className="metric-subtext">
          {isCleaned ? (
            missingCount === 0 ? (
              <span style={{ color: '#ffffff', fontWeight: 600 }}>0 celdas vacías</span>
            ) : (
              `${missingCount} valores nulos`
            )
          ) : (
            `${initialInspection?.rows_with_missing || 0} filas afectadas`
          )}
        </div>
      </div>

      {/* Duplicados Restantes */}
      <div className="metric-card">
        <div className="metric-header">
          <span>Filas Duplicadas</span>
          <div className="metric-icon">
            <CheckCircle size={16} />
          </div>
        </div>
        <div className="metric-value">
          {duplicateCount}
        </div>
        <div className="metric-subtext">
          {isCleaned ? (
            <span style={{ color: '#ffffff', fontWeight: 600 }}>
              0 duplicados
            </span>
          ) : (
            duplicateCount > 0 ? `${duplicateCount} identificados` : 'Sin duplicados'
          )}
        </div>
      </div>
    </div>
  );
}
