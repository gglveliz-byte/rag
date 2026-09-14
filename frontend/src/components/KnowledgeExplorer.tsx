import React, { useEffect, useState } from 'react';
import { FileText, Trash2, Tag, ChevronDown, ChevronUp, Eye, Database } from 'lucide-react';
import { deleteDocument, getDocumentDetails, listDocuments } from '../services/api';
import { ChunkItem, DocumentItem } from '../types';

export const KnowledgeExplorer: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [chunks, setChunks] = useState<ChunkItem[]>([]);
  const [chunksLoading, setChunksLoading] = useState(false);

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleToggleDetails = async (docId: string) => {
    if (selectedDocId === docId) {
      setSelectedDocId(null);
      setChunks([]);
      return;
    }

    setSelectedDocId(docId);
    setChunksLoading(true);
    try {
      const res = await getDocumentDetails(docId);
      setChunks(res.chunks || []);
    } catch (err) {
      console.error('Error loading chunks:', err);
    } finally {
      setChunksLoading(false);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`¿Eliminar definitivamente el documento "${filename}" y todos sus vectores asociados?`)) {
      return;
    }

    try {
      await deleteDocument(docId);
      if (selectedDocId === docId) {
        setSelectedDocId(null);
        setChunks([]);
      }
      fetchDocs();
    } catch (err) {
      console.error('Error deleting document:', err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <span className="badge badge-info" style={{ marginBottom: 'var(--space-2)' }}>
            <Database size={12} /> Memoria Indexada
          </span>
          <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 600 }}>Explorador de Documentos y Chunks</h2>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-1)' }}>
            Inspecciona los documentos vectorizados, sus etiquetas y los chunks generados por el particionador semántico.
          </p>
        </div>

        <button onClick={fetchDocs} className="btn btn-secondary">
          Actualizar
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--color-text-secondary)' }}>
          Cargando base de conocimiento...
        </div>
      ) : documents.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--color-text-tertiary)' }}>
          No hay documentos indexados en este espacio de trabajo. Sube un archivo o enlace de Drive para comenzar.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {documents.map((doc) => {
            const isExpanded = selectedDocId === doc.document_id;

            return (
              <div key={doc.document_id} className="card" style={{ padding: 'var(--space-4)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                    <div style={{ padding: 'var(--space-2)', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)' }}>
                      <FileText size={20} color="var(--color-text-primary)" />
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 'var(--text-sm)' }}>{doc.filename}</div>
                      <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center', marginTop: 'var(--space-1)', flexWrap: 'wrap' }}>
                        <span className="badge" style={{ fontSize: '0.65rem' }}>{doc.file_type}</span>
                        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>
                          {(doc.file_size_bytes / 1024).toFixed(1)} KB
                        </span>
                        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>•</span>
                        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-white)', fontWeight: 500 }}>
                          {doc.total_chunks} Chunks
                        </span>
                        {doc.tags?.map((t, idx) => (
                          <span key={idx} className="badge" style={{ fontSize: '0.65rem' }}>
                            <Tag size={10} /> {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                    <button
                      onClick={() => handleToggleDetails(doc.document_id)}
                      className="btn btn-secondary"
                      style={{ padding: '0.4rem 0.8rem', fontSize: 'var(--text-xs)' }}
                    >
                      <Eye size={13} />
                      {isExpanded ? 'Ocultar Chunks' : 'Ver Chunks'}
                      {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                    </button>

                    <button
                      onClick={() => handleDelete(doc.document_id, doc.filename)}
                      className="btn btn-danger"
                      style={{ padding: '0.4rem 0.8rem' }}
                      title="Eliminar documento y vectores"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

                {/* Expanded Chunks list */}
                {isExpanded && (
                  <div style={{ marginTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-4)' }}>
                    <h4 style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: 'var(--tracking-wider)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-3)' }}>
                      Fragmentos Semánticos ({chunks.length})
                    </h4>

                    {chunksLoading ? (
                      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>Cargando chunks...</div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', maxHeight: '380px', overflowY: 'auto' }}>
                        {chunks.map((ch) => (
                          <div
                            key={ch.chunk_id}
                            style={{
                              padding: 'var(--space-3)',
                              background: 'var(--color-bg-input)',
                              border: '1px solid var(--color-border)',
                              borderRadius: 'var(--radius-md)',
                              fontSize: 'var(--text-xs)',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-text-tertiary)', marginBottom: 'var(--space-1)' }}>
                              <span style={{ fontFamily: 'var(--font-mono)' }}>Chunk #{ch.chunk_index + 1}</span>
                              <span>{ch.token_count} tokens est.</span>
                            </div>
                            <div style={{ color: 'var(--color-text-primary)', lineHeight: 1.5 }}>
                              {ch.content}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
