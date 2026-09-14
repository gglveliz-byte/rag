import React, { useState } from 'react';
import { Search, Copy, Check, FileText, Clock, Sparkles } from 'lucide-react';
import { searchKnowledge } from '../services/api';
import { SearchResultItem, SystemHealth } from '../types';

interface SearchPanelProps {
  health?: SystemHealth | null;
}

export const SearchPanel: React.FC<SearchPanelProps> = ({ health }) => {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [scoreThreshold, setScoreThreshold] = useState(0.5);
  const [targetStore, setTargetStore] = useState<'postgres' | 'mongo' | 'both'>('postgres');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [queryTime, setQueryTime] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);

  React.useEffect(() => {
    if (health?.mongo_connected && !health?.postgres_connected) {
      setTargetStore('mongo');
    }
  }, [health]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await searchKnowledge(query, topK, targetStore, scoreThreshold);
      setResults(res.results);
      setQueryTime(res.query_time_ms);
    } catch (err) {
      console.error('Error during search:', err);
    } finally {
      setLoading(false);
    }
  };

  const copyPromptContext = () => {
    if (results.length === 0) return;
    const contextLines = results.map((r, i) => {
      const pageStr = r.metadata?.page_number ? ` (Página ${r.metadata.page_number})` : '';
      return `[Fragmento ${i + 1} - Fuente: ${r.source_file}${pageStr}]:\n${r.content}`;
    });
    navigator.clipboard.writeText(contextLines.join('\n\n---\n\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Search Input Card */}
      <div className="card">
        <form onSubmit={handleSearch} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div style={{ position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
            <input
              type="text"
              required
              placeholder="Realiza una consulta semántica (ej: ¿Cuáles son las cláusulas de rescisión?)..."
              className="input-field"
              style={{ paddingLeft: '44px', fontSize: 'var(--text-base)', height: '52px' }}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          {/* Search Controls (Sliders & Store) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-4)', padding: 'var(--space-3) 0', borderTop: '1px solid var(--color-border)', borderBottom: '1px solid var(--color-border)' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
                <span>Top K (Resultados)</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{topK}</span>
              </div>
              <input
                type="range"
                min={1}
                max={20}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--color-white)' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
                <span>Umbral Mínimo de Similitud</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{scoreThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min={0.0}
                max={1.0}
                step={0.05}
                value={scoreThreshold}
                onChange={(e) => setScoreThreshold(Number(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--color-white)' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
                Motor de Base Vectorial
              </label>
              <select
                className="input-field"
                style={{ padding: '0.4rem 0.6rem', fontSize: 'var(--text-xs)' }}
                value={targetStore}
                onChange={(e) => setTargetStore(e.target.value as any)}
              >
                <option value="postgres">PostgreSQL (pgvector)</option>
                <option value="mongo">MongoDB (Vector Search)</option>
                <option value="both">Multi-Base (Ambas)</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>
              {queryTime !== null && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  <Clock size={12} /> Búsqueda completada en {queryTime} ms ({results.length} coincidencias)
                </span>
              )}
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              {results.length > 0 && (
                <button
                  type="button"
                  onClick={copyPromptContext}
                  className="btn btn-secondary"
                  title="Copiar texto formateado para inyectar en prompt de LLM"
                >
                  {copied ? <Check size={14} color="var(--color-accent-success)" /> : <Copy size={14} />}
                  {copied ? 'Contexto Copiado' : 'Copiar Contexto RAG'}
                </button>
              )}

              <button type="submit" className="btn btn-primary" disabled={loading}>
                <Sparkles size={14} />
                {loading ? 'Buscando...' : 'Buscar'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Results List */}
      {results.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {results.map((item) => (
            <div key={item.chunk_id} className="card" style={{ padding: 'var(--space-4)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <FileText size={15} color="var(--color-text-secondary)" />
                  <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600 }}>{item.source_file}</span>
                  {item.metadata?.page_number && (
                    <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
                      Pág. {item.metadata.page_number}
                    </span>
                  )}
                </div>

                <span
                  className="badge badge-success"
                  style={{
                    fontSize: '0.75rem',
                    background: 'rgba(16, 185, 129, 0.1)',
                  }}
                >
                  {(item.score * 100).toFixed(1)}% Similitud
                </span>
              </div>

              <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-primary)', lineHeight: 1.6, whiteSpace: 'pre-wrap', background: 'var(--color-bg-input)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                {item.content}
              </div>
            </div>
          ))}
        </div>
      ) : queryTime !== null ? (
        <div className="card" style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--color-text-tertiary)', fontSize: 'var(--text-sm)' }}>
          No se encontraron fragmentos que superen el umbral de similitud seleccionado ({scoreThreshold.toFixed(2)}).
        </div>
      ) : null}
    </div>
  );
};
