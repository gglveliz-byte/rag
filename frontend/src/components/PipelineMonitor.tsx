import React, { useEffect, useState } from 'react';
import { Activity, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { JobSSEClient } from '../services/sse';
import { JobItem } from '../types';

interface PipelineMonitorProps {
  jobId: string | null;
  onFinished?: () => void;
}

export const PipelineMonitor: React.FC<PipelineMonitorProps> = ({ jobId, onFinished }) => {
  const [jobState, setJobState] = useState<Partial<JobItem>>({
    progress: 0,
    status: 'queued',
    stage_message: 'Iniciando conexión...',
  });
  const [logs, setLogs] = useState<Array<{ time: string; msg: string; stage: string }>>([]);

  useEffect(() => {
    if (!jobId) return;

    setLogs([]);
    const client = new JobSSEClient(
      jobId,
      (event) => {
        setJobState(event);
        if (event.stage_message) {
          const nowStr = new Date().toLocaleTimeString();
          setLogs((prev) => [
            ...prev,
            { time: nowStr, msg: event.stage_message || '', stage: event.status || 'running' },
          ]);
        }
      },
      () => {
        onFinished?.();
      },
      (err) => {
        console.error('SSE connection error:', err);
      }
    );

    client.connect();

    return () => {
      client.close();
    };
  }, [jobId]);

  if (!jobId) {
    return null;
  }

  const stages = [
    { key: 'extracting', label: 'Extracción' },
    { key: 'chunking', label: 'Semantic Chunking' },
    { key: 'embedding', label: 'Vectorización' },
    { key: 'storing', label: 'Almacenamiento' },
  ];

  const getStageStatus = (stageKey: string) => {
    if (jobState.status === 'completed') return 'completed';
    if (jobState.status === 'failed') return 'failed';
    if (jobState.status === stageKey) return 'active';
    const stageOrder = ['queued', 'extracting', 'chunking', 'embedding', 'storing', 'completed'];
    const currentIndex = stageOrder.indexOf(jobState.status || 'queued');
    const thisIndex = stageOrder.indexOf(stageKey);
    return currentIndex > thisIndex ? 'completed' : 'pending';
  };

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <Activity size={16} color="var(--color-accent-info)" />
          <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 'var(--tracking-wider)' }}>
            Monitor del Pipeline en Tiempo Real (SSE)
          </h3>
        </div>
        <span
          className={`badge ${
            jobState.status === 'completed'
              ? 'badge-success'
              : jobState.status === 'failed'
              ? 'badge-warning'
              : 'badge-info'
          }`}
        >
          {jobState.status === 'completed' ? (
            <CheckCircle2 size={12} />
          ) : jobState.status === 'failed' ? (
            <AlertCircle size={12} />
          ) : (
            <Loader2 size={12} className="spin" />
          )}
          {jobState.status}
        </span>
      </div>

      {/* Progress bar */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
          <span>{jobState.stage_message}</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--color-white)' }}>
            {jobState.progress}%
          </span>
        </div>
        <div className="progress-bar-container">
          <div className="progress-bar-fill" style={{ width: `${jobState.progress}%` }} />
        </div>
      </div>

      {/* HUD Stages Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
        {stages.map((st) => {
          const status = getStageStatus(st.key);
          const isActive = status === 'active';
          const isDone = status === 'completed';

          return (
            <div
              key={st.key}
              style={{
                padding: 'var(--space-3)',
                background: isActive ? 'var(--color-bg-elevated)' : 'var(--color-bg-input)',
                border: `1px solid ${isActive ? 'var(--color-accent-info)' : isDone ? 'rgba(16, 185, 129, 0.3)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-2)',
              }}
            >
              <span
                className="status-dot"
                style={{
                  background: isDone
                    ? 'var(--color-accent-success)'
                    : isActive
                    ? 'var(--color-accent-info)'
                    : 'var(--color-gray-600)',
                }}
              />
              <span style={{ fontSize: 'var(--text-xs)', fontWeight: isActive ? 600 : 400, color: isDone || isActive ? 'var(--color-white)' : 'var(--color-text-tertiary)' }}>
                {st.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Real-time event log */}
      {logs.length > 0 && (
        <div style={{ maxHeight: '120px', overflowY: 'auto', background: 'var(--color-bg-input)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-2) var(--space-3)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
          {logs.map((l, idx) => (
            <div key={idx} style={{ color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
              <span style={{ color: 'var(--color-text-tertiary)', marginRight: '6px' }}>[{l.time}]</span>
              <span style={{ color: 'var(--color-white)' }}>{l.msg}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
