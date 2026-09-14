import React, { useEffect, useState } from 'react';
import {
  UploadCloud,
  Search,
  Database,
  Archive,
  Key,
  LogIn,
  LogOut,
  Clock,
  ShieldCheck,
  Cpu,
  Layers,
  Home,
  X,
  Bot,
  HelpCircle,
} from 'lucide-react';
import { AuthModal } from './components/AuthModal';
import { AgentChat } from './components/AgentChat';
import { ApiKeysManager } from './components/ApiKeysManager';
import { BackupManager } from './components/BackupManager';
import { DriveImporter } from './components/DriveImporter';
import { FileUploader } from './components/FileUploader';
import { KnowledgeExplorer } from './components/KnowledgeExplorer';
import { LandingPage } from './components/LandingPage';
import { PipelineMonitor } from './components/PipelineMonitor';
import { SearchPanel } from './components/SearchPanel';
import { exportBackup, getSystemHealth, getUserProfile, logoutUser } from './services/api';
import { SystemHealth, UserProfile } from './types';

interface NavItemInfo {
  id: string;
  title: string;
  badge: string;
  shortDesc: string;
  details: string;
}

const NAV_ITEMS_INFO: Record<string, NavItemInfo> = {
  upload: {
    id: 'upload',
    title: 'Subir Archivo',
    badge: 'Ingesta Local',
    shortDesc: 'Carga y vectorización de archivos locales (PDF, Word, Excel, CSV, TXT, MD).',
    details: 'Extrae texto y metadatos, aplica segmentación semántica adaptativa con detección de cortes temáticos y calcula vectores densos (1024 dimensiones) para almacenamiento en base de datos.',
  },
  drive: {
    id: 'drive',
    title: 'Google Drive',
    badge: 'Cloud Import',
    shortDesc: 'Importación directa de documentos públicos desde enlaces de Google Drive.',
    details: 'Descarga e indexa archivos públicos directamente en tu base de datos vectorial sin necesidad de guardarlos primero en tu dispositivo local.',
  },
  search: {
    id: 'search',
    title: 'Búsqueda Semántica',
    badge: 'Recuperación Vectorial',
    shortDesc: 'Consultas semánticas directas por similitud matemática de vectores.',
    details: 'Convierte tu pregunta en un vector denso y localiza los fragmentos más afines de tus documentos, permitiendo configurar umbrales de coincidencia y cantidad de resultados (Top-K).',
  },
  chat: {
    id: 'chat',
    title: 'Agente IA (Chat)',
    badge: 'Cero Alucinación',
    shortDesc: 'Asistente conversacional inteligente que razona sobre tus documentos.',
    details: 'Responde preguntas de forma natural y fluida con parafraseo humano. Dispone de modo "Extractos Precisos" (Top-K) y "Toda la Base" (análisis integral en bruto) sin inventar información externa.',
  },
  knowledge: {
    id: 'knowledge',
    title: 'Explorador Memoria',
    badge: 'Inspección de Chunks',
    shortDesc: 'Visor técnico de documentos y fragmentos vectorizados.',
    details: 'Permite examinar cada fragmento, su contenido, metadatos y la representación numérica vectorial densa (1024 dimensiones) con terminal HUD de inspección.',
  },
  backup: {
    id: 'backup',
    title: 'Respaldos (.ragpkg)',
    badge: 'Portabilidad Total',
    shortDesc: 'Exportación e importación de paquetes portables comprimidos.',
    details: 'Descarga un paquete .ragpkg agnóstico con tus documentos y vectores ya calculados, facilitando migraciones entre bases de datos vectoriales sin recalcular embeddings.',
  },
  apikeys: {
    id: 'apikeys',
    title: 'API Keys para LLM',
    badge: 'Consumo Externo',
    shortDesc: 'Gestión de credenciales seguras para conectar tus propios agentes externos.',
    details: 'Permite generar claves API de alta entropía (rke_live_...) con ejemplos listos para copiar en Python, cURL y JavaScript para consultar el motor RAG desde tus aplicaciones.',
  },
};

export const App: React.FC = () => {
  const [viewMode, setViewMode] = useState<'landing' | 'workspace'>('landing');
  const [activeTab, setActiveTab] = useState<'upload' | 'drive' | 'search' | 'knowledge' | 'backup' | 'apikeys' | 'chat'>('upload');
  const [activeInfoItem, setActiveInfoItem] = useState<NavItemInfo | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [showAuthBanner, setShowAuthBanner] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register' | 'claim'>('login');
  const [health, setHealth] = useState<SystemHealth | null>(null);

  const checkAuth = async (showNotification = false) => {
    const profile = await getUserProfile();
    setUserProfile(profile);
    if (profile && showNotification) {
      setShowAuthBanner(true);
    }
  };

  useEffect(() => {
    if (showAuthBanner) {
      const timer = setTimeout(() => setShowAuthBanner(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [showAuthBanner]);

  const checkHealth = async () => {
    try {
      const h = await getSystemHealth();
      setHealth(h);
    } catch {
      // Ignored if backend starting up
    }
  };

  useEffect(() => {
    checkAuth();
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logoutUser();
    setUserProfile(null);
  };

  const openClaimModal = () => {
    setAuthMode('claim');
    setAuthModalOpen(true);
  };

  const enterEngineWithTab = (tab?: string) => {
    if (tab && ['upload', 'drive', 'search', 'knowledge', 'backup', 'apikeys'].includes(tab)) {
      setActiveTab(tab as any);
    }
    setViewMode('workspace');
  };

  // If in Landing Page mode, render the high-end Swiss futuristic engineering landing
  if (viewMode === 'landing') {
    return (
      <>
        <LandingPage
          onEnterEngine={enterEngineWithTab}
          onOpenAuth={() => {
            setAuthMode('login');
            setAuthModalOpen(true);
          }}
          userEmail={userProfile?.email}
        />
        <AuthModal
          isOpen={authModalOpen}
          initialMode={authMode}
          onClose={() => setAuthModalOpen(false)}
          onAuthSuccess={() => {
            checkAuth(true);
          }}
        />
      </>
    );
  }

  // Otherwise, render the Engine Workspace in Studio White theme
  return (
    <div className="app-container">
      {/* Sidebar for Desktop */}
      <aside className="sidebar">
        <div>
          {/* Brand Logo */}
          <div
            onClick={() => setViewMode('landing')}
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-6)', padding: 'var(--space-2)', cursor: 'pointer' }}
            title="Ir al inicio"
          >
            <div style={{ width: '32px', height: '32px', background: 'var(--color-black)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Cpu size={16} color="var(--color-white)" />
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: 'var(--text-xs)', letterSpacing: 'var(--tracking-widest)', textTransform: 'uppercase', color: 'var(--color-black)' }}>
                KNOWLEDGE
              </div>
              <div style={{ fontSize: '0.65rem', color: 'var(--color-text-tertiary)', letterSpacing: '0.12em' }}>
                VECTOR ENGINE
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', flex: 1 }}>
          <button
            onClick={() => setActiveTab('upload')}
            className={`nav-item ${activeTab === 'upload' ? 'active' : ''}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <UploadCloud size={16} /> Subir Archivo
            </div>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.upload);
              }}
              className="nav-help-icon"
              title="¿Qué es Subir Archivo?"
            >
              ?
            </span>
          </button>

          <button
            onClick={() => setActiveTab('drive')}
            className={`nav-item ${activeTab === 'drive' ? 'active' : ''}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <Layers size={16} /> Google Drive
            </div>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.drive);
              }}
              className="nav-help-icon"
              title="¿Qué es Google Drive?"
            >
              ?
            </span>
          </button>

          <button
            onClick={() => setActiveTab('search')}
            className={`nav-item ${activeTab === 'search' ? 'active' : ''}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <Search size={16} /> Búsqueda Semántica
            </div>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.search);
              }}
              className="nav-help-icon"
              title="¿Qué es Búsqueda Semántica?"
            >
              ?
            </span>
          </button>

          <button
            onClick={() => setActiveTab('chat')}
            className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <Bot size={16} /> Agente IA (Chat)
            </div>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.chat);
              }}
              className="nav-help-icon"
              title="¿Qué es Agente IA (Chat)?"
            >
              ?
            </span>
          </button>

          <button
            onClick={() => setActiveTab('knowledge')}
            className={`nav-item ${activeTab === 'knowledge' ? 'active' : ''}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <Database size={16} /> Explorador Memoria
            </div>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.knowledge);
              }}
              className="nav-help-icon"
              title="¿Qué es Explorador Memoria?"
            >
              ?
            </span>
          </button>

          <button
            onClick={() => setActiveTab('backup')}
            className={`nav-item ${activeTab === 'backup' ? 'active' : ''}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <Archive size={16} /> Respaldos (.ragpkg)
            </div>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.backup);
              }}
              className="nav-help-icon"
              title="¿Qué son Respaldos (.ragpkg)?"
            >
              ?
            </span>
          </button>

          <button
            onClick={() => {
              if (!userProfile) {
                setAuthMode('login');
                setAuthModalOpen(true);
              } else {
                setActiveTab('apikeys');
              }
            }}
            className={`nav-item ${activeTab === 'apikeys' ? 'active' : ''}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <Key size={16} /> API Keys para LLM
            </div>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.apikeys);
              }}
              className="nav-help-icon"
              title="¿Qué son API Keys para LLM?"
            >
              ?
            </span>
          </button>
        </nav>
      </aside>

      {/* Main Content Viewport */}
      <div className="main-content">
        {/* Top Notification Banner: Guest vs Authenticated (Auto-dismissing) */}
        {!userProfile ? (
          <div className="ephemeral-banner">
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Clock size={16} />
              <span>
                <strong>Modo Invitado (Sandbox de 24 horas):</strong> Tus documentos y vectores expirarán automáticamente. Descarga tu backup o vincula tus datos a una cuenta permanente para obtener tu API Key para LLMs.
              </span>
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-2)', flexShrink: 0 }}>
              <button
                onClick={exportBackup}
                className="btn btn-secondary"
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.7rem' }}
              >
                Descargar Backup
              </button>
              <button
                onClick={openClaimModal}
                className="btn btn-primary"
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.7rem' }}
              >
                Vincular a Cuenta Permanente
              </button>
            </div>
          </div>
        ) : showAuthBanner ? (
          <div style={{
            padding: '0.45rem 1.25rem',
            background: '#ECFDF5',
            borderBottom: '1px solid #A7F3D0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.78rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#065F46' }}>
              <ShieldCheck size={15} color="#059669" />
              <span>Sesión iniciada con éxito como <strong>{userProfile.email}</strong>. Tus datos están guardados de forma permanente en PostgreSQL Neon.</span>
            </div>
            <button
              onClick={() => setShowAuthBanner(false)}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#065F46', display: 'flex', alignItems: 'center', padding: '4px' }}
              title="Cerrar notificación"
            >
              <X size={14} />
            </button>
          </div>
        ) : null}

        {/* Topbar Header */}
        <header className="topbar-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <button
              onClick={() => setViewMode('landing')}
              className="btn btn-secondary"
              style={{ padding: '0.45rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              title="Ir al inicio"
            >
              <Home size={16} />
            </button>

            <div style={{ fontSize: 'var(--text-sm)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)', color: 'var(--color-black)' }}>
              {activeTab === 'upload' && 'Ingesta de Archivos'}
              {activeTab === 'drive' && 'Importador de Google Drive'}
              {activeTab === 'search' && 'Búsqueda Semántica'}
              {activeTab === 'chat' && 'Agente IA Especializado'}
              {activeTab === 'knowledge' && 'Explorador de Memoria'}
              {activeTab === 'backup' && 'Respaldos Portables'}
              {activeTab === 'apikeys' && 'Gestión de API Keys'}
            </div>
          </div>

          <div>
            {!userProfile ? (
              <button
                onClick={() => { setAuthMode('login'); setAuthModalOpen(true); }}
                className="btn btn-primary"
                style={{ padding: '0.45rem 0.95rem' }}
              >
                <LogIn size={14} /> Acceder
              </button>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setActiveTab('apikeys')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 10px',
                    background: '#F1F5F9',
                    border: '1px solid #E2E8F0',
                    borderRadius: '20px',
                    fontSize: '0.74rem',
                    color: '#334155',
                    cursor: 'pointer'
                  }}
                  title="Ver perfil y claves API"
                >
                  <ShieldCheck size={13} color="#059669" />
                  <span style={{ fontWeight: 600, maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {userProfile.email}
                  </span>
                </button>
                <button
                  onClick={handleLogout}
                  className="btn btn-secondary"
                  style={{ padding: '0.42rem 0.8rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '5px' }}
                  title="Cerrar sesión"
                >
                  <LogOut size={13} /> <span>Salir</span>
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Mobile Navigation Tabs Bar (Visible on mobile/tablets when sidebar is hidden) */}
        <nav className="mobile-tab-nav" aria-label="Navegación móvil del Workspace">
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`mobile-tab-item ${activeTab === 'upload' ? 'active' : ''}`}
          >
            <UploadCloud size={14} /> <span>Subir Archivo</span>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.upload);
              }}
              className="mobile-help-bubble"
              title="Información sobre Subir Archivo"
            >
              ?
            </span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('drive')}
            className={`mobile-tab-item ${activeTab === 'drive' ? 'active' : ''}`}
          >
            <Layers size={14} /> <span>Google Drive</span>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.drive);
              }}
              className="mobile-help-bubble"
              title="Información sobre Google Drive"
            >
              ?
            </span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('search')}
            className={`mobile-tab-item ${activeTab === 'search' ? 'active' : ''}`}
          >
            <Search size={14} /> <span>Búsqueda</span>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.search);
              }}
              className="mobile-help-bubble"
              title="Información sobre Búsqueda"
            >
              ?
            </span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('chat')}
            className={`mobile-tab-item ${activeTab === 'chat' ? 'active' : ''}`}
          >
            <Bot size={14} /> <span>Agente IA</span>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.chat);
              }}
              className="mobile-help-bubble"
              title="Información sobre Agente IA"
            >
              ?
            </span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('knowledge')}
            className={`mobile-tab-item ${activeTab === 'knowledge' ? 'active' : ''}`}
          >
            <Database size={14} /> <span>Memoria</span>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.knowledge);
              }}
              className="mobile-help-bubble"
              title="Información sobre Memoria"
            >
              ?
            </span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('backup')}
            className={`mobile-tab-item ${activeTab === 'backup' ? 'active' : ''}`}
          >
            <Archive size={14} /> <span>Respaldos</span>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.backup);
              }}
              className="mobile-help-bubble"
              title="Información sobre Respaldos"
            >
              ?
            </span>
          </button>
          <button
            type="button"
            onClick={() => {
              if (!userProfile) {
                setAuthMode('login');
                setAuthModalOpen(true);
              } else {
                setActiveTab('apikeys');
              }
            }}
            className={`mobile-tab-item ${activeTab === 'apikeys' ? 'active' : ''}`}
          >
            <Key size={14} /> <span>API Keys</span>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setActiveInfoItem(NAV_ITEMS_INFO.apikeys);
              }}
              className="mobile-help-bubble"
              title="Información sobre API Keys"
            >
              ?
            </span>
          </button>
        </nav>

        {/* Body Container */}
        <main className="content-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {/* Active Job SSE Progress Monitor (scoped to upload tabs with close capability) */}
          {activeJobId && (activeTab === 'upload' || activeTab === 'drive') && (
            <PipelineMonitor
              jobId={activeJobId}
              onFinished={() => checkHealth()}
              onClose={() => setActiveJobId(null)}
            />
          )}

          {/* Active Tab View */}
          {activeTab === 'upload' && (
            <FileUploader
              onJobStarted={(id) => setActiveJobId(id)}
              health={health}
            />
          )}

          {activeTab === 'drive' && (
            <DriveImporter
              onJobStarted={(id) => setActiveJobId(id)}
              health={health}
            />
          )}

          {activeTab === 'search' && <SearchPanel health={health} />}

          {activeTab === 'chat' && <AgentChat onNavigateToUpload={() => setActiveTab('upload')} />}

          {activeTab === 'knowledge' && <KnowledgeExplorer />}

          {activeTab === 'backup' && <BackupManager health={health} />}

          {activeTab === 'apikeys' && <ApiKeysManager />}
        </main>
      </div>

      {/* Help / Information Modal for Navigation Items */}
      {activeInfoItem && (
        <div
          onClick={() => setActiveInfoItem(null)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.5)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '1.25rem',
            animation: 'fadeIn 0.15s ease-out',
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: '#FFFFFF',
              borderRadius: '16px',
              padding: '1.5rem',
              maxWidth: '440px',
              width: '100%',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
              border: '1px solid #E2E8F0',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
              <span
                style={{
                  fontSize: '0.68rem',
                  padding: '3px 8px',
                  borderRadius: '6px',
                  background: '#F1F5F9',
                  color: '#475569',
                  fontWeight: 700,
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                }}
              >
                {activeInfoItem.badge}
              </span>
              <button
                onClick={() => setActiveInfoItem(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#94A3B8',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '4px',
                  borderRadius: '6px',
                }}
                title="Cerrar"
              >
                <X size={16} />
              </button>
            </div>

            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <HelpCircle size={18} color="#2563EB" />
              ¿Qué es {activeInfoItem.title}?
            </h3>

            <p style={{ fontSize: '0.85rem', color: '#1E293B', lineHeight: 1.55, marginBottom: '0.75rem', fontWeight: 500 }}>
              {activeInfoItem.shortDesc}
            </p>

            <div style={{ fontSize: '0.78rem', color: '#64748B', lineHeight: 1.6, marginBottom: '1.25rem', background: '#F8FAFC', padding: '0.85rem', borderRadius: '10px', border: '1px solid #F1F5F9' }}>
              {activeInfoItem.details}
            </div>

            <button
              onClick={() => setActiveInfoItem(null)}
              style={{
                width: '100%',
                padding: '0.65rem',
                background: '#0F172A',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '10px',
                fontWeight: 600,
                fontSize: '0.82rem',
                cursor: 'pointer',
              }}
            >
              Entendido
            </button>
          </div>
        </div>
      )}

      {/* Auth / Claim Modal */}
      <AuthModal
        isOpen={authModalOpen}
        initialMode={authMode}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={() => {
          checkAuth();
        }}
      />
    </div>
  );
};
