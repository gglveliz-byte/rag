import React from 'react';
import { Database, Check } from 'lucide-react';
import { SystemHealth } from '../types';

interface TargetStoreSelectorProps {
  selectedStore: 'postgres' | 'mongo' | 'both';
  onChange: (store: 'postgres' | 'mongo' | 'both') => void;
  health?: SystemHealth | null;
}

export const TargetStoreSelector: React.FC<TargetStoreSelectorProps> = ({
  selectedStore,
  onChange,
  health,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      <label style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
        <Database size={13} /> Base de Datos Vectorial de Destino
      </label>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 'var(--space-2)' }}>
        {/* PostgreSQL Option */}
        <button
          type="button"
          onClick={() => onChange('postgres')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.65rem 0.85rem',
            background: selectedStore === 'postgres' ? 'var(--color-bg-elevated)' : 'var(--color-bg-input)',
            border: `1px solid ${selectedStore === 'postgres' ? 'var(--color-white)' : 'var(--color-border)'}`,
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
            fontSize: 'var(--text-xs)',
            fontWeight: 500,
            transition: 'all 0.2s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span className={`status-dot ${health?.postgres_connected ? 'online' : 'offline'}`} />
            <span>PostgreSQL</span>
          </div>
          {selectedStore === 'postgres' && <Check size={14} />}
        </button>

        {/* MongoDB Option */}
        <button
          type="button"
          onClick={() => onChange('mongo')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.65rem 0.85rem',
            background: selectedStore === 'mongo' ? 'var(--color-bg-elevated)' : 'var(--color-bg-input)',
            border: `1px solid ${selectedStore === 'mongo' ? 'var(--color-white)' : 'var(--color-border)'}`,
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
            fontSize: 'var(--text-xs)',
            fontWeight: 500,
            transition: 'all 0.2s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span className={`status-dot ${health?.mongo_connected ? 'online' : 'offline'}`} />
            <span>MongoDB</span>
          </div>
          {selectedStore === 'mongo' && <Check size={14} />}
        </button>

        {/* Both Option */}
        <button
          type="button"
          onClick={() => onChange('both')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.65rem 0.85rem',
            background: selectedStore === 'both' ? 'var(--color-bg-elevated)' : 'var(--color-bg-input)',
            border: `1px solid ${selectedStore === 'both' ? 'var(--color-white)' : 'var(--color-border)'}`,
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
            fontSize: 'var(--text-xs)',
            fontWeight: 500,
            transition: 'all 0.2s ease',
          }}
        >
          <span>Multi-Destino (Ambas)</span>
          {selectedStore === 'both' && <Check size={14} />}
        </button>
      </div>
    </div>
  );
};
