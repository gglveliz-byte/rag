import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  FileText,
  ShieldCheck,
  Info,
  Activity,
  Cpu,
  Layers,
  Search,
} from 'lucide-react';
import { sendChatMessage, fetchChatSuggestions } from '../services/api';
import { ChatMessage } from '../types';

interface AgentChatProps {
  onNavigateToUpload?: () => void;
}

export const AgentChat: React.FC<AgentChatProps> = ({ onNavigateToUpload }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});
  const [expandedTelemetry, setExpandedTelemetry] = useState<Record<string, boolean>>({});
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([
    '¿Qué es NeuroChat y quién es su fundador?',
    '¿Cuáles son los canales de mensajería soportados?',
    '¿Cómo funciona el módulo de ventas y validación por IA Vision?',
    '¿Cuáles son las medidas de seguridad y aislamiento multi-tenant?',
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    // Fetch dynamic suggestions from active tenant documents
    fetchChatSuggestions()
      .then((suggestions) => {
        if (suggestions && suggestions.length > 0) {
          setSuggestedPrompts(suggestions);
        }
      })
      .catch(() => {
        // Retain default prompts if offline or empty
      });
  }, []);

  const toggleCitation = (msgId: string) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  const toggleTelemetry = (msgId: string) => {
    setExpandedTelemetry((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText || inputValue).trim();
    if (!textToSend || loading) return;

    const userMessageId = `user_${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMessageId,
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!queryText) setInputValue('');
    setLoading(true);

    try {
      const responseData = await sendChatMessage({
        query: textToSend,
        top_k: 5,
        score_threshold: 0.45,
      });

      const assistantMessageId = `assistant_${Date.now()}`;
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: responseData.answer,
        citations: responseData.citations,
        has_grounding: responseData.has_grounding,
        is_conversational: responseData.is_conversational,
        primary_source: responseData.primary_source,
        primary_score: responseData.primary_score,
        model: responseData.model,
        execution_time_ms: responseData.execution_time_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Automatically expand citations if grounded
      if (responseData.has_grounding && responseData.citations.length > 0) {
        setExpandedCitations((prev) => ({ ...prev, [assistantMessageId]: true }));
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al comunicarse con el Agente RAG.';
      const errorMessage: ChatMessage = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        content: `⚠️ ${errorMsg}`,
        has_grounding: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setExpandedCitations({});
    setExpandedTelemetry({});
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', height: 'calc(100vh - 170px)', minHeight: '520px' }}>
      {/* Top Banner / Agent Header */}
      <div className="card" style={{ padding: '0.85rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: '#0F172A',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF'
          }}>
            <Bot size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '0.98rem', fontWeight: 700, margin: 0, letterSpacing: '-0.02em', color: 'var(--color-black)' }}>
                Agente IA Especializado (Qwen 3.8 Flash)
              </h2>
              <span className="badge badge-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.68rem', padding: '2px 8px' }}>
                <ShieldCheck size={11} />
                CERO ALUCINACIÓN
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '0.74rem', color: 'var(--color-text-secondary)' }}>
              Respuestas naturales y fluidas delimitadas de forma estricta a tu base de conocimiento.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleClearChat}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '0.45rem 0.85rem',
            background: '#FFFFFF',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.75rem',
            fontWeight: 600,
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = '#000000';
            e.currentTarget.style.color = 'var(--color-black)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-border)';
            e.currentTarget.style.color = 'var(--color-text-secondary)';
          }}
        >
          <RotateCcw size={13} />
          <span>LIMPIAR CHAT</span>
        </button>
      </div>

      {/* Main Conversation Container */}
      <div className="card" style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        padding: '1.25rem',
        overflow: 'hidden',
        background: '#FAFAFA'
      }}>
        {/* Messages Scroll Area */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          paddingRight: '6px'
        }}>
          {messages.length === 0 ? (
            /* Empty State with Dynamic Prompts */
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              padding: '2rem 1rem',
              color: 'var(--color-text-secondary)'
            }}>
              <div style={{
                width: '54px',
                height: '54px',
                borderRadius: '16px',
                background: '#FFFFFF',
                border: '1px solid var(--color-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem',
                boxShadow: '0 4px 12px rgba(0,0,0,0.04)'
              }}>
                <Sparkles size={26} color="var(--color-accent-info)" />
              </div>

              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--color-black)', margin: '0 0 6px 0' }}>
                Hazle una pregunta a tu base de conocimiento
              </h3>
              <p style={{ fontSize: '0.82rem', maxWidth: '480px', lineHeight: 1.5, margin: '0 0 16px 0' }}>
                El agente consulta tu memoria vectorial en tiempo real y sintetiza respuestas naturales respaldadas por citas.
                {onNavigateToUpload && (
                  <span style={{ display: 'block', marginTop: '6px' }}>
                    <button
                      type="button"
                      onClick={onNavigateToUpload}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--color-accent-info)',
                        textDecoration: 'underline',
                        cursor: 'pointer',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        padding: 0
                      }}
                    >
                      + Subir nuevos documentos al motor
                    </button>
                  </span>
                )}
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxWidth: '460px', width: '100%' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--color-text-tertiary)' }}>
                  Preguntas sugeridas (extraídas de tus documentos):
                </span>
                {suggestedPrompts.map((prompt, pIdx) => (
                  <button
                    key={pIdx}
                    onClick={() => handleSend(prompt)}
                    style={{
                      padding: '0.65rem 1rem',
                      background: '#FFFFFF',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.8rem',
                      color: 'var(--color-text-primary)',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#000000';
                      e.currentTarget.style.transform = 'translateY(-1px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--color-border)';
                      e.currentTarget.style.transform = 'none';
                    }}
                  >
                    💬 {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '100%'
                }}
              >
                {/* Bubble Wrapper */}
                <div style={{
                  display: 'flex',
                  gap: '10px',
                  maxWidth: msg.role === 'user' ? '82%' : '88%',
                  alignItems: 'flex-start',
                  flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
                }}>
                  {/* Avatar */}
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '8px',
                    background: msg.role === 'user' ? '#0F172A' : '#FFFFFF',
                    border: '1px solid var(--color-border)',
                    color: msg.role === 'user' ? '#FFFFFF' : 'var(--color-accent-info)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px'
                  }}>
                    {msg.role === 'user' ? <User size={15} /> : <Bot size={15} />}
                  </div>

                  {/* Message Card */}
                  <div style={{
                    padding: '0.85rem 1.15rem',
                    borderRadius: '14px',
                    background: msg.role === 'user' ? '#0F172A' : '#FFFFFF',
                    color: msg.role === 'user' ? '#FFFFFF' : 'var(--color-text-primary)',
                    border: msg.role === 'user' ? 'none' : '1px solid var(--color-border)',
                    boxShadow: msg.role === 'user' ? '0 4px 12px rgba(15, 23, 42, 0.15)' : '0 2px 8px rgba(0,0,0,0.03)',
                    fontSize: '0.85rem',
                    lineHeight: 1.6,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word'
                  }}>
                    {msg.content}

                    {/* Metadata Footer */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginTop: '8px',
                      fontSize: '0.68rem',
                      color: msg.role === 'user' ? 'rgba(255,255,255,0.6)' : '#94A3B8',
                      borderTop: msg.role === 'user' ? '1px solid rgba(255,255,255,0.1)' : '1px solid #F1F5F9',
                      paddingTop: '6px'
                    }}>
                      <span>{msg.timestamp}</span>
                      {msg.model && <span>• {msg.model}</span>}
                      {msg.execution_time_ms && (
                        <span>• {Math.round(msg.execution_time_ms)}ms</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Protective Zero-Hallucination Disclaimers & Telemetry */}
                {msg.role === 'assistant' && (
                  <div style={{ marginLeft: '38px', marginTop: '6px', maxWidth: '85%', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    
                    {/* Badge 1: Grounded in docs */}
                    {msg.has_grounding && (
                      <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.72rem',
                        color: '#065F46',
                        background: '#ECFDF5',
                        padding: '3px 9px',
                        borderRadius: '6px',
                        border: '1px solid #A7F3D0'
                      }}>
                        <ShieldCheck size={12} color="#059669" />
                        <span>
                          Respuesta protegida por Cero Alucinación: el dato figura en el archivo: <strong>{msg.primary_source || msg.citations?.[0]?.filename || 'documento'}</strong> {msg.primary_score ? `(${msg.primary_score}% similitud)` : ''}
                        </span>
                      </div>
                    )}

                    {/* Badge 2: Conversational Expression */}
                    {msg.is_conversational && (
                      <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.72rem',
                        color: '#1E40AF',
                        background: '#EFF6FF',
                        padding: '3px 9px',
                        borderRadius: '6px',
                        border: '1px solid #BFDBFE'
                      }}>
                        <Sparkles size={12} color="#3B82F6" />
                        <span>
                          Este dato no está explícitamente en la base de conocimiento: es una expresión natural de la LLM (saludo / cortesía).
                        </span>
                      </div>
                    )}

                    {/* Badge 3: Out-of-knowledge question */}
                    {!msg.has_grounding && !msg.is_conversational && (
                      <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.72rem',
                        color: '#92400E',
                        background: '#FFFBEB',
                        padding: '3px 9px',
                        borderRadius: '6px',
                        border: '1px solid #FDE68A'
                      }}>
                        <Info size={12} color="#D97706" />
                        <span>Respuesta protegida por Cero Alucinación: el dato no figura en tus documentos.</span>
                      </div>
                    )}

                    {/* Action buttons row: Citations + Telemetry */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginTop: '2px' }}>
                      {msg.citations && msg.citations.length > 0 && (
                        <button
                          type="button"
                          onClick={() => toggleCitation(msg.id)}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '3px 9px',
                            background: '#FFFFFF',
                            border: '1px solid var(--color-border)',
                            borderRadius: '20px',
                            fontSize: '0.71rem',
                            fontWeight: 600,
                            color: 'var(--color-text-secondary)',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease'
                          }}
                        >
                          <FileText size={11} color="var(--color-accent-info)" />
                          <span>{msg.citations.length} fuentes consultadas</span>
                          {expandedCitations[msg.id] ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => toggleTelemetry(msg.id)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '3px 9px',
                          background: '#FFFFFF',
                          border: '1px solid var(--color-border)',
                          borderRadius: '20px',
                          fontSize: '0.71rem',
                          fontWeight: 600,
                          color: 'var(--color-text-secondary)',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease'
                        }}
                      >
                        <Activity size={11} color="#6366F1" />
                        <span>Vista previa: ¿Cómo actúa por detrás?</span>
                        {expandedTelemetry[msg.id] ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                      </button>
                    </div>

                    {/* Citations Accordion */}
                    {expandedCitations[msg.id] && msg.citations && (
                      <div style={{
                        marginTop: '4px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px',
                        padding: '10px',
                        background: '#FFFFFF',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '0.76rem'
                      }}>
                        {msg.citations.map((c, cIdx) => (
                          <div key={c.chunk_id || cIdx} style={{
                            padding: '8px 10px',
                            background: '#F8FAFC',
                            border: '1px solid #E2E8F0',
                            borderRadius: '6px'
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                              <span style={{ fontWeight: 600, color: 'var(--color-black)' }}>
                                📄 {c.filename}
                              </span>
                              <span style={{ fontSize: '0.68rem', fontWeight: 600, color: '#059669', background: '#ECFDF5', padding: '1px 6px', borderRadius: '4px' }}>
                                {Math.round(c.similarity_score * 100)}% coincidencia
                              </span>
                            </div>
                            <div style={{ color: '#475569', fontStyle: 'italic', lineHeight: 1.4 }}>
                              "{c.content}"
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Telemetry Accordion (Detrás de escena) */}
                    {expandedTelemetry[msg.id] && (
                      <div style={{
                        marginTop: '4px',
                        padding: '12px',
                        background: '#0F172A',
                        color: '#E2E8F0',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '0.74rem',
                        lineHeight: 1.6,
                        boxShadow: '0 4px 14px rgba(0,0,0,0.12)'
                      }}>
                        <div style={{ fontWeight: 700, color: '#38BDF8', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Cpu size={13} />
                          <span>FLUJO INTERNO RAG (DETRÁS DE ESCENA)</span>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px' }}>
                          <div style={{ background: 'rgba(255,255,255,0.05)', padding: '8px', borderRadius: '6px' }}>
                            <div style={{ color: '#94A3B8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <Layers size={11} /> 1. Vectorización
                            </div>
                            <div>DashScope text-embedding-v3 (1024 dims)</div>
                          </div>
                          <div style={{ background: 'rgba(255,255,255,0.05)', padding: '8px', borderRadius: '6px' }}>
                            <div style={{ color: '#94A3B8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <Search size={11} /> 2. Búsqueda Vectorial
                            </div>
                            <div>MongoDB Atlas & Postgres HNSW Coseno</div>
                          </div>
                          <div style={{ background: 'rgba(255,255,255,0.05)', padding: '8px', borderRadius: '6px' }}>
                            <div style={{ color: '#94A3B8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <ShieldCheck size={11} /> 3. Filtro Cero Alucinación
                            </div>
                            <div>{msg.citations?.length || 0} fragmentos con similitud &gt;= 45%</div>
                          </div>
                          <div style={{ background: 'rgba(255,255,255,0.05)', padding: '8px', borderRadius: '6px' }}>
                            <div style={{ color: '#94A3B8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <Bot size={11} /> 4. Síntesis Grounded
                            </div>
                            <div>Qwen 3.8 Flash ({msg.execution_time_ms ? `${Math.round(msg.execution_time_ms)}ms` : 'tiempo real'})</div>
                          </div>
                        </div>
                      </div>
                    )}

                  </div>
                )}
              </div>
            ))
          )}

          {/* Typing Indicator while bot is generating */}
          {loading && (
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginLeft: '2px' }}>
              <div style={{
                width: '28px',
                height: '28px',
                borderRadius: '8px',
                background: '#FFFFFF',
                border: '1px solid var(--color-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-accent-info)'
              }}>
                <Bot size={15} />
              </div>
              <div className="bot-typing-bubble">
                <div className="typing-dots">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
                <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
                  El bot está consultando tus documentos y escribiendo...
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar Area */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{
            marginTop: 'var(--space-3)',
            display: 'flex',
            gap: '8px',
            background: '#FFFFFF',
            padding: '6px 8px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border)',
            boxShadow: '0 2px 6px rgba(0,0,0,0.02)'
          }}
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Pregúntale cualquier cosa a tu base de conocimiento..."
            disabled={loading}
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              padding: '0.5rem 0.75rem',
              fontSize: '0.85rem',
              background: 'transparent',
              color: 'var(--color-black)'
            }}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: inputValue.trim() && !loading ? '#000000' : '#E2E8F0',
              color: inputValue.trim() && !loading ? '#FFFFFF' : '#94A3B8',
              border: 'none',
              cursor: inputValue.trim() && !loading ? 'pointer' : 'not-allowed',
              transition: 'all 0.15s ease'
            }}
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </div>
  );
};
