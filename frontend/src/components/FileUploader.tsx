import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertCircle, RefreshCw } from 'lucide-react';
import { uploadFile } from '../services/api';
import { TargetStoreSelector } from './TargetStoreSelector';
import { SystemHealth } from '../types';

interface FileUploaderProps {
  onJobStarted: (jobId: string) => void;
  health?: SystemHealth | null;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onJobStarted, health }) => {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [targetStore, setTargetStore] = useState<'postgres' | 'mongo' | 'both'>('postgres');
  const [tags, setTags] = useState('');
  const [loading, setLoading] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (health?.mongo_connected && !health?.postgres_connected) {
      setTargetStore('mongo');
    }
  }, [health]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelected = (file: File) => {
    setError(null);
    setDuplicateWarning(null);
    const validExtensions = ['.pdf', '.docx', '.xlsx', '.csv', '.txt', '.md'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!validExtensions.includes(ext)) {
      setError(`Formato no soportado (${ext}). Formatos válidos: ${validExtensions.join(', ')}`);
      return;
    }
    setSelectedFile(file);
  };

  const handleUpload = async (forceReplace: boolean = false) => {
    if (!selectedFile) return;
    setLoading(true);
    setError(null);
    setDuplicateWarning(null);

    try {
      const res = await uploadFile(selectedFile, targetStore, tags, forceReplace);
      onJobStarted(res.job_id);
      setSelectedFile(null);
      setTags('');
    } catch (err: any) {
      if (err.response?.status === 409) {
        setDuplicateWarning(err.response.data.detail || 'Este archivo ya fue indexado previamente en tu base vectorial.');
      } else {
        setError(err.response?.data?.detail || 'Error al iniciar la ingesta del archivo.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div>
        <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600 }}>Subida de Documentos Locales</h3>
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-1)' }}>
          Formatos compatibles: PDF, Word (.docx), Excel (.xlsx), CSV, Texto plano y Markdown.
        </p>
      </div>

      <TargetStoreSelector
        selectedStore={targetStore}
        onChange={setTargetStore}
        health={health}
      />

      {/* Drag & Drop Area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragOver ? 'var(--color-white)' : 'var(--color-border)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-8)',
          textAlign: 'center',
          cursor: 'pointer',
          background: dragOver ? 'var(--color-bg-hover)' : 'var(--color-bg-input)',
          transition: 'all 0.2s ease',
        }}
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
          accept=".pdf,.docx,.xlsx,.csv,.txt,.md"
        />
        <UploadCloud size={32} color="var(--color-text-secondary)" style={{ margin: '0 auto var(--space-2)' }} />
        <div style={{ fontSize: 'var(--text-sm)', fontWeight: 500 }}>
          {selectedFile ? selectedFile.name : 'Arrastra un documento aquí o haz clic para explorar'}
        </div>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)', marginTop: 'var(--space-1)' }}>
          {selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB` : 'Máximo 500 MB'}
        </div>
      </div>

      {/* Tags Input */}
      <div>
        <label style={{ display: 'block', fontSize: 'var(--text-xs)', textTransform: 'uppercase', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
          Etiquetas (Opcional, separadas por coma)
        </label>
        <input
          type="text"
          placeholder="ej: legal, finanzas, manuales, q3"
          className="input-field"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
        />
      </div>

      {/* Duplicate Warning */}
      {duplicateWarning && (
        <div style={{ padding: 'var(--space-3)', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--color-accent-warning)', fontSize: 'var(--text-xs)' }}>
            <AlertCircle size={14} /> {duplicateWarning}
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => handleUpload(true)}
            style={{ alignSelf: 'flex-start', fontSize: '0.7rem' }}
          >
            <RefreshCw size={12} /> Reemplazar e indexar de nuevo
          </button>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div style={{ padding: 'var(--space-3)', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-md)', color: 'var(--color-accent-error)', fontSize: 'var(--text-xs)' }}>
          {error}
        </div>
      )}

      {/* Upload button */}
      <button
        type="button"
        className="btn btn-primary"
        disabled={!selectedFile || loading}
        onClick={() => handleUpload(false)}
        style={{ marginTop: 'var(--space-2)' }}
      >
        <FileText size={14} />
        {loading ? 'Iniciando Pipeline...' : 'Iniciar Ingesta y Vectorización'}
      </button>
    </div>
  );
};
