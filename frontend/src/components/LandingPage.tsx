import React from 'react';
import { ArrowRight, User, LogIn } from 'lucide-react';

interface LandingPageProps {
  onEnterEngine: (initialTab?: string) => void;
  onOpenAuth?: () => void;
  userEmail?: string | null;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onEnterEngine,
  onOpenAuth,
  userEmail,
}) => {
  return (
    <div
      className="landing-image-wrapper"
      onContextMenu={(e) => e.preventDefault()}
    >
      {/* Marco envolvente con la imagen responsiva de alta definición */}
      <div className="landing-image-canvas">
        {/* Imagen protegida: no se puede copiar, arrastrar ni interactuar */}
        <picture className="landing-picture">
          <source media="(max-width: 768px)" srcSet="/assets/landing_hero_mobile.png" />
          <source media="(min-width: 769px)" srcSet="/assets/landing_hero_full.png" />
          <img
            src="/assets/landing_hero_full.png"
            alt="Knowledge Engine — Memoria Vectorial para RAG"
            className="landing-backdrop-image"
            draggable={false}
            onContextMenu={(e) => e.preventDefault()}
            onDragStart={(e) => e.preventDefault()}
          />
        </picture>

        {/* Botón táctil sobre el icono de menú de la versión móvil */}
        <button
          type="button"
          className="btn-mobile-menu-target"
          onClick={onOpenAuth}
          aria-label="Iniciar sesión o registrarse"
          title="Iniciar sesión"
        />

        {/* Acciones flotantes de escritorio (Top Bar) */}
        <header className="landing-overlay-topbar">
          <div className="topbar-actions">
            <button
              type="button"
              className="btn-overlay-login"
              onClick={onOpenAuth}
              title={userEmail ? `Sesión iniciada como ${userEmail}` : 'Iniciar sesión'}
            >
              {userEmail ? <User size={13} /> : <LogIn size={13} />}
              <span className="mono">{userEmail ? userEmail.split('@')[0].toUpperCase() : 'INICIAR SESIÓN'}</span>
            </button>

            <button
              type="button"
              className="btn-overlay-start"
              onClick={() => onEnterEngine('upload')}
              title="Comenzar a usar el motor RAG"
            >
              <span className="mono">COMENZAR AHORA</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </header>

        {/* Dock flotante ergonómico para versión móvil */}
        <div className="landing-mobile-dock">
          <button
            type="button"
            className="btn-overlay-login"
            onClick={onOpenAuth}
            title={userEmail ? `Sesión iniciada como ${userEmail}` : 'Iniciar sesión'}
          >
            {userEmail ? <User size={12} /> : <LogIn size={12} />}
            <span className="mono">{userEmail ? userEmail.split('@')[0].toUpperCase() : 'INICIAR SESIÓN'}</span>
          </button>

          <button
            type="button"
            className="btn-overlay-start"
            onClick={() => onEnterEngine('upload')}
            title="Comenzar a usar el motor RAG"
          >
            <span className="mono">COMENZAR AHORA</span>
            <ArrowRight size={12} />
          </button>
        </div>
      </div>
    </div>
  );
};
