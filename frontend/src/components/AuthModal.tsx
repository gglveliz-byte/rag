import React, { useState } from 'react';
import { X, Lock, Mail, ArrowRight, ShieldCheck, Eye, EyeOff, UserPlus, LogIn, AlertCircle, CheckCircle2 } from 'lucide-react';
import { claimGuestSession, getGuestSessionId, loginUser, registerUser } from '../services/api';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: () => void;
  initialMode?: 'login' | 'register' | 'claim';
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onAuthSuccess,
  initialMode = 'login',
}) => {
  const [mode, setMode] = useState<'login' | 'register' | 'claim'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const isRegister = mode === 'register' || mode === 'claim';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (isRegister && password !== confirmPassword) {
      setError('Las contraseñas no coinciden. Por favor verifícalas.');
      return;
    }

    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.');
      return;
    }

    setLoading(true);

    try {
      if (mode === 'login') {
        await loginUser(email, password);
        onAuthSuccess();
        onClose();
      } else {
        // Register mode or Claim mode
        await registerUser(email, password);
        const guestSessId = getGuestSessionId();
        if (guestSessId) {
          try {
            await claimGuestSession(guestSessId);
          } catch (cErr) {
            console.warn('Could not claim session automatically:', cErr);
          }
        }
        onAuthSuccess();
        onClose();
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Error de autenticación. Verifique sus credenciales.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Top bar with security badge & close button */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: '20px',
            background: '#F1F5F9',
            border: '1px solid #E2E8F0',
            fontSize: '0.72rem',
            fontWeight: 600,
            color: '#0F172A',
            letterSpacing: '0.04em',
            textTransform: 'uppercase'
          }}>
            <ShieldCheck size={13} color="#059669" /> Acceso Seguro
          </span>
          <button
            type="button"
            className="auth-close-btn"
            onClick={onClose}
            title="Cerrar ventana"
          >
            <X size={16} />
          </button>
        </div>

        {/* Segmented Tab Switcher (Iniciar Sesión vs Crear Cuenta) */}
        <div className="auth-segmented-tabs">
          <button
            type="button"
            className={`auth-segmented-tab ${!isRegister ? 'active' : ''}`}
            onClick={() => { setMode('login'); setError(null); }}
          >
            <LogIn size={14} /> Iniciar Sesión
          </button>
          <button
            type="button"
            className={`auth-segmented-tab ${isRegister ? 'active' : ''}`}
            onClick={() => { setMode('register'); setError(null); }}
          >
            <UserPlus size={14} /> Crear Cuenta
          </button>
        </div>

        {/* Header Titles */}
        <div style={{ marginBottom: '1.25rem' }}>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#0F172A', letterSpacing: '-0.02em', margin: 0 }}>
            {mode === 'login' ? 'Bienvenido de nuevo' : mode === 'claim' ? 'Vincular Espacio de Trabajo' : 'Crear Cuenta Empresarial'}
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#64748B', marginTop: '0.35rem', lineHeight: 1.4, margin: '0.35rem 0 0 0' }}>
            {mode === 'login'
              ? 'Ingresa tus credenciales para acceder a tus documentos y vectores.'
              : mode === 'claim'
              ? 'Tus documentos temporales se guardarán de forma permanente en tu cuenta.'
              : 'Empieza a indexar documentos con memoria vectorial de alta precisión.'}
          </p>
        </div>

        {/* Error Callout */}
        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px',
            padding: '0.75rem 0.9rem',
            background: '#FEF2F2',
            border: '1px solid #FECACA',
            borderRadius: '10px',
            color: '#DC2626',
            fontSize: '0.8rem',
            marginBottom: '1rem',
            lineHeight: 1.35
          }}>
            <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{error}</span>
          </div>
        )}

        {/* Success Callout */}
        {successMsg && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '0.75rem 0.9rem',
            background: '#ECFDF5',
            border: '1px solid #A7F3D0',
            borderRadius: '10px',
            color: '#059669',
            fontSize: '0.8rem',
            marginBottom: '1rem'
          }}>
            <CheckCircle2 size={16} style={{ flexShrink: 0 }} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          {/* Email field */}
          <div className="auth-input-group">
            <label className="auth-input-label">
              Correo Electrónico
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }} />
              <input
                type="email"
                required
                className="auth-input-field"
                placeholder="nombre@empresa.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
              />
            </div>
          </div>

          {/* Password field */}
          <div className="auth-input-group">
            <label className="auth-input-label">
              Contraseña
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }} />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={6}
                className="auth-input-field"
                placeholder={isRegister ? 'Mínimo 6 caracteres' : '••••••••'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="auth-password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                title={showPassword ? 'Ocultar contraseña' : 'Ver contraseña'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Confirm Password field (only in register/claim mode) */}
          {isRegister && (
            <div className="auth-input-group">
              <label className="auth-input-label">
                Confirmar Contraseña
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }} />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  minLength={6}
                  className="auth-input-field"
                  placeholder="Repite tu contraseña"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  title={showConfirmPassword ? 'Ocultar contraseña' : 'Ver contraseña'}
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          )}

          {/* Submit Action */}
          <button
            type="submit"
            className="auth-submit-btn"
            disabled={loading}
          >
            {loading ? (
              <span>Procesando solicitud...</span>
            ) : (
              <>
                <span>{mode === 'login' ? 'Entrar a mi Espacio' : mode === 'claim' ? 'Vincular y Comenzar' : 'Crear Cuenta'}</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </form>

        {/* Security & Privacy Assurance Footer */}
        <div style={{
          marginTop: '1.25rem',
          paddingTop: '0.85rem',
          borderTop: '1px solid #F1F5F9',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '0.35rem',
          fontSize: '0.74rem',
          color: '#64748B',
          textAlign: 'center',
          lineHeight: 1.4
        }}>
          <span>🔒 Tu espacio es 100% privado. Solo tú tienes acceso a tus documentos y búsquedas.</span>
        </div>
      </div>
    </div>
  );
};
