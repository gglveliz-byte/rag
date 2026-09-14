import React, { useState, useRef } from 'react';
import { Archive, Download, UploadCloud, CheckCircle2, AlertCircle } from 'lucide-react';
import { exportBackup, importBackup } from '../services/api';
import { TargetStoreSelector } from './TargetStoreSelector';

import { SystemHealth } from '../types';

interface BackupManagerProps {
  health?: SystemHealth | null;
}

export const BackupManager: React.FC<BackupManagerProps> = ({ health }) => {
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [targetStore, setTargetStore] = useState<'postgres' | 'mongo' | 'both'>('postgres');
  const [importResult, setImportResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (health?.mongo_connected && !health?.postgres_connected) {
      setTargetStore('mongo');
    }
  }, [health]);

  const handleExport = async () => {
    setExporting(true);
    setError(null);
    try {
      await exportBackup();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al generar y descargar el respaldo .ragpkg.');
    } finally {
      setExporting(false);
    }
  };

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.ragpkg')) {
      setError('El archivo debe tener la extensión .ragpkg');
      return;
    }

    setImporting(true);
    setError(null);
    setImportResult(null);

    try {
      const res = await importBackup(file, targetStore);
      setImportResult(`Restauración exitosa: ${res.restored_documents} documentos y ${res.restored_chunks} chunks restaurados.`);
      if (fileRef.current) fileRef.current.value = '';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al restaurar el paquete de respaldo.');
    } finally {
      setImporting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Overview Card */}
      <div className="card">
        <span className="badge badge-info" style={{ marginBottom: 'var(--space-2)' }}>
          <Archive size={12} /> Respaldo Agnóstico
        </span>
        <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 600 }}>Exportación e Importación (.ragpkg)</h2>
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-1)', maxWidth: '700px' }}>
          El formato <code>.ragpkg</code> es un archivo comprimido portable (JSONL + Gzip) independiente de la infraestructura. Puedes descargarlo para conservarlo localmente o migrar tus vectores entre entornos.
        </p>
      </div>

      {error && (
        <div style={{ padding: 'var(--space-3)', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-md)', color: 'var(--color-accent-error)', fontSize: 'var(--text-xs)' }}>
          <AlertCircle size={14} style={{ display: 'inline', marginRight: '6px' }} />
          {error}
        </div>
      )}

      {importResult && (
        <div style={{ padding: 'var(--space-3)', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 'var(--radius-md)', color: 'var(--color-accent-success)', fontSize: 'var(--text-xs)' }}>
          <CheckCircle2 size={14} style={{ display: 'inline', marginRight: '6px' }} />
          {importResult}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--space-6)' }}>
        {/* Export Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600 }}>Descargar Respaldo Completo</h3>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-2)', lineHeight: 1.6 }}>
              Genera un archivo <code>.ragpkg</code> que incluye todos los documentos, metadatos, chunks y vectores calculados de tu sesión o cuenta activa.
            </p>
          </div>

          <button
            onClick={handleExport}
            className="btn btn-primary"
            disabled={exporting}
            style={{ marginTop: 'var(--space-6)' }}
          >
            <Download size={14} />
            {exporting ? 'Generando Paquete...' : 'Exportar Backup (.ragpkg)'}
          </button>
        </div>

        {/* Import Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div>
            <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600 }}>Restaurar Respaldo</h3>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-2)', lineHeight: 1.6 }}>
              Sube un paquete <code>.ragpkg</code> previo para indexar automáticamente sus vectores en la base seleccionada.
            </p>
          </div>

          <TargetStoreSelector
            selectedStore={targetStore}
            onChange={setTargetStore}
          />

          <input
            type="file"
            ref={fileRef}
            style={{ display: 'none' }}
            accept=".ragpkg"
            onChange={handleImportFile}
          />

          <button
            onClick={() => fileRef.current?.click()}
            className="btn btn-secondary"
            disabled={importing}
          >
            <UploadCloud size={14} />
            {importing ? 'Restaurando...' : 'Seleccionar archivo .ragpkg'}
          </button>
        </div>
      </div>
    </div>
  );
};
