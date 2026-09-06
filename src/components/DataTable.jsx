import React, { useState, useMemo } from 'react';
import { Table, Search, ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react';

export default function DataTable({
  data,
  columns,
  title = "Previsualización de Datos",
  isCleaned = false,
  onDeleteColumn,
  deletedColumns = [],
  onRestoreColumn,
  onRestoreAllColumns,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  // Filter rows based on search term
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return [];
    if (!searchTerm.trim()) return data;

    const term = searchTerm.toLowerCase();
    return data.filter(row => {
      return Object.values(row).some(val => {
        if (val === null || val === undefined) return false;
        return String(val).toLowerCase().includes(term);
      });
    });
  }, [data, searchTerm]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredData.length / pageSize));
  const currentPage = Math.min(page, totalPages - 1);
  const displayedRows = filteredData.slice(currentPage * pageSize, (currentPage + 1) * pageSize);

  // Column keys from first row or columns prop
  const colKeys = useMemo(() => {
    if (columns && columns.length > 0) {
      return columns.map(c => (typeof c === 'object' ? c.name : c));
    }
    if (data && data.length > 0) {
      return Object.keys(data[0]);
    }
    return [];
  }, [columns, data]);

  if (!data || data.length === 0) {
    return (
      <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No hay datos para previsualizar.
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ padding: '1.25rem 1.5rem', marginBottom: '2rem' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.85rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Table size={18} style={{ color: 'var(--text-secondary)' }} />
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>{title}</h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {filteredData.length} registros • {colKeys.length} columnas activas
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          {/* Search bar */}
          <div style={{ position: 'relative', minWidth: '200px' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '1.9rem', width: '100%', fontSize: '0.8rem' }}
              placeholder="Buscar..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(0);
              }}
            />
          </div>

          {/* Page size select */}
          <select
            className="form-select"
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.65rem' }}
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(0);
            }}
          >
            <option value={10}>10 filas</option>
            <option value={25}>25 filas</option>
            <option value={50}>50 filas</option>
          </select>
        </div>
      </div>

      {/* Deleted columns restore bar if any */}
      {isCleaned && deletedColumns && deletedColumns.length > 0 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          marginBottom: '1rem',
          padding: '0.6rem 0.85rem',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          flexWrap: 'wrap',
          fontSize: '0.8rem'
        }}>
          <span style={{ color: 'var(--text-muted)' }}>Columnas eliminadas:</span>
          {deletedColumns.map((col) => (
            <span key={col} className="col-restore-chip">
              <span>{col}</span>
              <button
                onClick={() => onRestoreColumn(col)}
                title={`Restaurar columna ${col}`}
              >
                + Restaurar
              </button>
            </span>
          ))}

          {deletedColumns.length > 1 && (
            <button
              onClick={onRestoreAllColumns}
              className="btn btn-secondary"
              style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem', marginLeft: 'auto' }}
            >
              <RotateCcw size={11} /> Restaurar todas
            </button>
          )}
        </div>
      )}

      {/* Table Wrapper */}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '40px', textAlign: 'center' }}>#</th>
              {colKeys.map((colName) => (
                <th key={colName}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.35rem' }}>
                    <span>{colName}</span>
                    {isCleaned && onDeleteColumn && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteColumn(colName);
                        }}
                        className="btn-delete-col"
                        title={`Eliminar columna "${colName}"`}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayedRows.length === 0 ? (
              <tr>
                <td colSpan={colKeys.length + 1} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No se encontraron filas coincidentes.
                </td>
              </tr>
            ) : (
              displayedRows.map((row, rIdx) => (
                <tr key={rIdx}>
                  <td style={{ textAlign: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                    {currentPage * pageSize + rIdx + 1}
                  </td>
                  {colKeys.map((colName) => {
                    const val = row[colName];
                    const isNull = val === null || val === undefined;

                    return (
                      <td key={colName}>
                        {isNull ? (
                          <span className="cell-null">vacío</span>
                        ) : (
                          String(val)
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1rem', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
        <div>
          Página <strong style={{ color: 'var(--text-primary)' }}>{currentPage + 1}</strong> de{' '}
          <strong style={{ color: 'var(--text-primary)' }}>{totalPages}</strong>
        </div>

        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <button
            className="btn btn-secondary"
            style={{ padding: '0.3rem 0.65rem', fontSize: '0.78rem' }}
            disabled={currentPage === 0}
            onClick={() => setPage(p => Math.max(0, p - 1))}
          >
            <ChevronLeft size={14} /> Anterior
          </button>
          <button
            className="btn btn-secondary"
            style={{ padding: '0.3rem 0.65rem', fontSize: '0.78rem' }}
            disabled={currentPage >= totalPages - 1}
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
          >
            Siguiente <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
