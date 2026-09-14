import React, { useEffect, useState } from 'react';
import { Key, Plus, Copy, Check, Trash2, ShieldAlert, Sparkles, Server } from 'lucide-react';
import { createApiKey, listApiKeys, revokeApiKey } from '../services/api';
import { APIKeyItem } from '../types';

type CodeTab = 'curl' | 'python' | 'javascript';

export const ApiKeysManager: React.FC = () => {
  const [keys, setKeys] = useState<APIKeyItem[]>([]);
  const [keyName, setKeyName] = useState('');
  const [loading, setLoading] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [activeTab, setActiveTab] = useState<CodeTab>('curl');

  const fetchKeys = async () => {
    try {
      const data = await listApiKeys();
      setKeys(data);
    } catch (err) {
      console.error('Error fetching API keys:', err);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim()) return;
    setLoading(true);
    try {
      const created = await createApiKey(keyName);
      setNewlyCreatedKey(created.raw_key || null);
      setKeyName('');
      fetchKeys();
    } catch (err) {
      console.error('Error creating key:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (keyId: string) => {
    if (!confirm('¿Estás seguro de revocar esta API Key? Los LLMs o agentes externos que la usen perderán acceso de inmediato.')) {
      return;
    }
    try {
      await revokeApiKey(keyId);
      fetchKeys();
    } catch (err) {
      console.error('Error revoking key:', err);
    }
  };

  const copyToClipboard = (text: string, type: 'key' | 'code') => {
    navigator.clipboard.writeText(text);
    if (type === 'key') {
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2500);
    } else {
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2500);
    }
  };

  // Dynamically resolve backend endpoint based on current host & port
  const getDynamicApiUrl = () => {
    const envBase = import.meta.env.VITE_API_URL;
    if (envBase) {
      return envBase.replace(/\/api\/?$/, '').replace(/\/+$/, '');
    }
    if (typeof window !== 'undefined') {
      // In local dev with Vite on port 5173, backend is on port 8000
      if (window.location.port === '5173') {
        return `${window.location.protocol}//${window.location.hostname}:8000`;
      }
      return window.location.origin;
    }
    return 'http://localhost:8000';
  };

  const dynamicEndpoint = `${getDynamicApiUrl()}/api/v1/rag/query`;
  const currentKeyPlaceholder = newlyCreatedKey || (keys.length > 0 ? keys[0].masked_key : 'rke_live_TU_API_KEY');

  const getCodeSnippet = () => {
    if (activeTab === 'curl') {
      return `curl -X POST "${dynamicEndpoint}" \\
  -H "Authorization: Bearer ${currentKeyPlaceholder}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "¿Cuáles son las cláusulas de garantía del contrato?",
    "top_k": 5,
    "score_threshold": 0.75
  }'`;
    }

    if (activeTab === 'python') {
      return `import requests

url = "${dynamicEndpoint}"
headers = {
    "Authorization": "Bearer ${currentKeyPlaceholder}",
    "Content-Type": "application/json"
}
payload = {
    "query": "¿Cuáles son las cláusulas de garantía del contrato?",
    "top_k": 5,
    "score_threshold": 0.75
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

# Imprimir los fragmentos recuperados para alimentar el contexto de tu LLM
print(f"Total de fragmentos: {len(data.get('chunks', []))}")
print("Contexto formateado para prompt:\n", data.get("context_string"))`;
    }

    return `// Consumo desde Node.js o frontend moderno (Fetch API)
const response = await fetch("${dynamicEndpoint}", {
  method: "POST",
  headers: {
    "Authorization": "Bearer ${currentKeyPlaceholder}",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    query: "¿Cuáles son las cláusulas de garantía del contrato?",
    top_k: 5,
    score_threshold: 0.75
  })
});

const data = await response.json();
console.log("Contexto listo para LLM:", data.context_string);`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header & Generator Card */}
      <div className="card" style={{ padding: 'var(--space-6)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: 'var(--space-2)' }}>
              <span className="badge badge-info" style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '3px 8px' }}>
                <Key size={12} /> Integración Externa
              </span>
              <span style={{ fontSize: '0.72rem', color: 'var(--color-text-tertiary)' }}>
                Protocolo REST seguro (Bearer Token)
              </span>
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.01em', color: 'var(--color-black)' }}>
              Gestión de API Keys para LLMs y Agentes
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginTop: '4px', maxWidth: '640px', lineHeight: 1.5 }}>
              Genera credenciales seguras para consultar tu memoria vectorial privada desde ChatGPT, Claude, LangChain, Cursor, n8n o tus propias aplicaciones.
            </p>
          </div>

          {/* Creation Form */}
          <form onSubmit={handleCreate} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="text"
              placeholder="Nombre (ej: Agente Legal)"
              className="input-field"
              style={{ width: '220px', padding: '0.55rem 0.85rem', fontSize: '0.82rem' }}
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              required
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0.55rem 1rem', fontSize: '0.82rem' }}
            >
              <Plus size={15} /> {loading ? 'Generando...' : 'Crear Clave'}
            </button>
          </form>
        </div>

        {/* Newly created raw key alert (Stripe-style secret reveal) */}
        {newlyCreatedKey && (
          <div style={{
            marginTop: 'var(--space-5)',
            padding: '1rem 1.25rem',
            background: '#F0FDF4',
            border: '1px solid #86EFAC',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#166534', fontSize: '0.82rem', fontWeight: 600 }}>
                <Sparkles size={16} color="#16A34A" />
                <span>Clave de Acceso Generada con Éxito</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#B45309', fontSize: '0.74rem' }}>
                <ShieldAlert size={14} />
                <span>Cópiala ahora. Por seguridad, no se volverá a mostrar completa.</span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <code style={{
                flex: 1,
                padding: '0.65rem 1rem',
                background: '#FFFFFF',
                border: '1px solid #BBF7D0',
                borderRadius: 'var(--radius-md)',
                fontFamily: 'monospace',
                fontSize: '0.85rem',
                color: '#15803D',
                fontWeight: 600,
                overflowX: 'auto',
                letterSpacing: '0.02em'
              }}>
                {newlyCreatedKey}
              </code>
              <button
                onClick={() => copyToClipboard(newlyCreatedKey, 'key')}
                className="btn btn-primary"
                style={{ padding: '0.65rem 1.1rem', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}
              >
                {copiedKey ? <Check size={15} /> : <Copy size={15} />}
                <span>{copiedKey ? '¡Copiada!' : 'Copiar Clave'}</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Active Keys Table / List Card */}
      <div className="card" style={{ padding: 'var(--space-6)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
          <h3 style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, color: 'var(--color-black)' }}>
            Claves Activas ({keys.length})
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
            Aislamiento estricto por usuario en PostgreSQL Neon
          </span>
        </div>

        {keys.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '2.5rem 1rem',
            background: '#F8FAFC',
            border: '1px dashed var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            color: 'var(--color-text-secondary)',
            fontSize: '0.85rem'
          }}>
            <Key size={24} style={{ margin: '0 auto 8px auto', opacity: 0.4 }} />
            <div style={{ fontWeight: 600, color: 'var(--color-black)' }}>No tienes claves de API activas</div>
            <div style={{ fontSize: '0.78rem', marginTop: '4px' }}>Crea tu primera clave arriba para conectar tus agentes o LLMs externos.</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {keys.map((k) => (
              <div
                key={k.key_id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.85rem 1.1rem',
                  background: '#FFFFFF',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  transition: 'border-color 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    background: '#F1F5F9',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#0F172A'
                  }}>
                    <Key size={15} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--color-black)' }}>{k.name}</span>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem', color: '#16A34A', fontWeight: 600 }}>
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#16A34A' }} /> Activa
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginTop: '3px' }}>
                      <code style={{ fontSize: '0.76rem', color: '#64748B', fontFamily: 'monospace', background: '#F8FAFC', padding: '2px 6px', borderRadius: '4px' }}>
                        {k.masked_key}
                      </code>
                      <span style={{ fontSize: '0.72rem', color: '#94A3B8' }}>
                        Creada el {new Date(k.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleRevoke(k.key_id)}
                  className="btn"
                  style={{
                    padding: '0.4rem 0.75rem',
                    fontSize: '0.75rem',
                    color: '#EF4444',
                    background: '#FEF2F2',
                    border: '1px solid #FEE2E2',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px'
                  }}
                  title="Revocar acceso a esta clave"
                >
                  <Trash2 size={13} /> <span>Revocar</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Code Snippet integration card — Modern Swiss Studio Terminal */}
      <div className="card" style={{ padding: '0', overflow: 'hidden', border: '1px solid #1E293B', background: '#090D16' }}>
        {/* Terminal Header */}
        <div style={{
          padding: '0.75rem 1.25rem',
          background: '#0F172A',
          borderBottom: '1px solid #1E293B',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          {/* Left: Window Dots & Endpoint indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#EF4444' }} />
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#F59E0B' }} />
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10B981' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.76rem', color: '#94A3B8' }}>
              <Server size={13} color="#38BDF8" />
              <span style={{ color: '#E2E8F0', fontWeight: 600 }}>POST</span>
              <span style={{ fontFamily: 'monospace', color: '#94A3B8' }}>{dynamicEndpoint}</span>
            </div>
          </div>

          {/* Right: Language Tabs & Copy Button */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ display: 'flex', background: '#1E293B', padding: '2px', borderRadius: '6px' }}>
              <button
                type="button"
                onClick={() => setActiveTab('curl')}
                style={{
                  padding: '4px 10px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  background: activeTab === 'curl' ? '#38BDF8' : 'transparent',
                  color: activeTab === 'curl' ? '#0F172A' : '#94A3B8',
                  transition: 'all 0.15s ease'
                }}
              >
                cURL
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('python')}
                style={{
                  padding: '4px 10px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  background: activeTab === 'python' ? '#38BDF8' : 'transparent',
                  color: activeTab === 'python' ? '#0F172A' : '#94A3B8',
                  transition: 'all 0.15s ease'
                }}
              >
                Python
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('javascript')}
                style={{
                  padding: '4px 10px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  background: activeTab === 'javascript' ? '#38BDF8' : 'transparent',
                  color: activeTab === 'javascript' ? '#0F172A' : '#94A3B8',
                  transition: 'all 0.15s ease'
                }}
              >
                JavaScript
              </button>
            </div>

            <button
              onClick={() => copyToClipboard(getCodeSnippet(), 'code')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '4px 10px',
                fontSize: '0.72rem',
                fontWeight: 600,
                color: copiedCode ? '#34D399' : '#F1F5F9',
                background: '#1E293B',
                border: '1px solid #334155',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              title="Copiar código al portapapeles"
            >
              {copiedCode ? <Check size={13} color="#34D399" /> : <Copy size={13} />}
              <span>{copiedCode ? '¡Copiado!' : 'Copiar'}</span>
            </button>
          </div>
        </div>

        {/* Terminal Body with Code */}
        <pre style={{
          margin: 0,
          padding: '1.25rem',
          fontSize: '0.8rem',
          color: '#E2E8F0',
          fontFamily: 'Consolas, Menlo, Monaco, "Courier New", monospace',
          lineHeight: 1.6,
          overflowX: 'auto',
          background: '#090D16'
        }}>
          {getCodeSnippet()}
        </pre>
      </div>
    </div>
  );
};
