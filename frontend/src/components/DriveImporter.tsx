import React, { useState } from 'react';
import { Link2, ArrowRight, AlertCircle } from 'lucide-react';
import { ingestDrive } from '../services/api';
import { TargetStoreSelector } from './TargetStoreSelector';
import { SystemHealth } from '../types';

interface DriveImporterProps {
  onJobStarted: (jobId: string) => void;
  health?: SystemHealth | null;
}

export const DriveImporter: React.FC<DriveImporterProps> = ({ onJobStarted, health }) => {
  const [driveUrl, setDriveUrl] = useState('');
  const [targetStore, setTargetStore] = useState<'postgres' | 'mongo' | 'both'>('postgres');
  const [tags, setTags] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (health?.mongo_connected && !health?.postgres_connected) {
      setTargetStore('mongo');
    }
  }, [health]);

  const isValidDriveUrl = (url: string): boolean => {
    return (
      url.includes('drive.google.com/file/d/') ||
      url.includes('drive.google.com/open?id=') ||
      url.includes('drive.google.com/uc?id=') ||
      url.length > 25
    );
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!driveUrl.trim()) return;

    if (!isValidDriveUrl(driveUrl)) {
      setError('Por favor ingresa un enlace público válido de Google Drive.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const targets = targetStore === 'both' ? ['postgres', 'mongo'] : [targetStore];
      const tagList = tags.split(',').map((t) => t.trim()).filter(Boolean);
      const res = await ingestDrive(driveUrl, targets, tagList, false);
      onJobStarted(res.job_id);
      setDriveUrl('');
      setTags('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al conectar con Google Drive.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div>
        <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600 }}>Importación desde Google Drive Público</h3>
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-1)' }}>
          Pega el enlace de un archivo público de Drive (PDF, Word, Excel, CSV o Texto). No requiere credenciales de API.
        </p>
      </div>

      <TargetStoreSelector
        selectedStore={targetStore}
        onChange={setTargetStore}
        health={health}
      />

      <form onSubmit={handleIngest} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <div>
          <label style={{ display: 'block', fontSize: 'var(--text-xs)', textTransform: 'uppercase', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
            Enlace de Google Drive
          </label>
          <div style={{ position: 'relative' }}>
            <Link2 size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
            <input
              type="url"
              required
              placeholder="https://drive.google.com/file/d/1A2B3C.../view?usp=sharing"
              className="input-field"
              style={{ paddingLeft: '38px' }}
              value={driveUrl}
              onChange={(e) => {
                setDriveUrl(e.target.value);
                setError(null);
              }}
            />
          </div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: 'var(--text-xs)', textTransform: 'uppercase', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
            Etiquetas (Opcional, separadas por coma)
          </label>
          <input
            type="text"
            placeholder="ej: drive, manuales, corporativo"
            className="input-field"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
          />
        </div>

        {error && (
          <div style={{ padding: 'var(--space-3)', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-md)', color: 'var(--color-accent-error)', fontSize: 'var(--text-xs)' }}>
            <AlertCircle size={14} style={{ display: 'inline', marginRight: '6px' }} />
            {error}
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={!driveUrl.trim() || loading}
          style={{ marginTop: 'var(--space-2)' }}
        >
          {loading ? 'Descargando e iniciando...' : 'Descargar e Indexar'}
          <ArrowRight size={14} />
        </button>
      </form>
    </div>
  );
};
