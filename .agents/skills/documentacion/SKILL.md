---
name: documentacion
description: Registro vivo y actualizado de todos los archivos del repositorio Knowledge Engine (RAG), sus responsabilidades, líneas de código y estado actual.
---

# Skill de Documentación Viva — Knowledge Engine (RAG)

Esta skill es el punto de referencia **obligatorio** antes y después de realizar modificaciones en el código.
Garantiza que ningún archivo supere las **800 líneas** y que la arquitectura se mantenga coherente.

---

## 1. Inventario de Frontend (`frontend/src/`)

| Archivo | Líneas Aprox. | Límite (<800) | Responsabilidad Principal |
| :--- | :---: | :---: | :--- |
| `src/main.tsx` | ~10 | ✅ OK | Punto de entrada ReactDOM. |
| `src/App.tsx` | ~429 | ✅ OK | Estado central de navegación, autenticación, banner de confirmación auto-removible, pestaña 'Agente IA' limpia en sidebar y navegación móvil. |
| `src/index.css` | ~685 | ✅ OK | Variables de diseño, reset, navegación móvil/desktop (`.mobile-tab-nav`, `.sidebar`), modales, y animación fluida de tipeo para el bot (`.bot-typing-bubble`, `.typing-dot`). |
| `src/landing.css` | ~180 | ✅ OK | Estilos de la Landing Page: responsividad móvil/desktop, dock flotante inferior y protección contra copiado/arrastre. |
| `src/types/index.ts` | ~127 | ✅ OK | Definiciones TypeScript: documentos, chunks, salud del sistema y payload de chat (`ChatMessage`, `ChatResponseData`, `CitationItem`). |
| `src/services/api.ts` | ~210 | ✅ OK | Cliente Axios con interceptor multi-tenant, endpoints de auth, ingestión, búsqueda semántica, `sendChatMessage` y `fetchChatSuggestions`. |
| `src/components/LandingPage.tsx` | ~85 | ✅ OK | Vista inicial responsiva: versión panorámica para desktop y vertical para móvil, imagen protegida e inerte, botones exclusivos de interacción. |
| `src/components/AgentChat.tsx` | ~585 | ✅ OK | Chat de Agente IA con diseño white-label limpio (sin exponer vendors ni stack), animación de tipeo en vivo, 3 niveles de disclaimers de Cero Alucinación, acordeón de citas y sugerencias dinámicas. |
| `src/components/PipelineMonitor.tsx` | ~184 | ✅ OK | Monitor SSE de ingesta con tarjetas de etapas de alto contraste (verde/azul/gris con textos oscuros legibles) y consola terminal oscura para eventos en vivo. |
| `src/components/FileUploader.tsx` | ~170 | ✅ OK | Panel de subida de archivos locales con autoselección inteligente de la base conectada (MongoDB Atlas / PostgreSQL). |
| `src/components/DriveImporter.tsx` | ~130 | ✅ OK | Importador de archivos públicos de Google Drive con autoselección de base conectada. |
| `src/components/SearchPanel.tsx` | ~190 | ✅ OK | Panel de consulta vectorial semántica con slider de umbral, top-k y autoselección de base activa. |
| `src/components/KnowledgeExplorer.tsx` | ~180 | ✅ OK | Explorador interactivo de chunks vectorizados con metadatos y copiado de contexto. |
| `src/components/BackupManager.tsx` | ~140 | ✅ OK | Panel de exportación e importación de paquetes `.ragpkg` agnósticos. |
| `src/components/ApiKeysManager.tsx` | ~310 | ✅ OK | Panel rediseñado de API Keys con terminal estilo macOS, URL backend 100% dinámica, tabs de lenguaje (cURL, Python, JS), copiado y gestión de claves. |
| `src/components/AuthModal.tsx` | ~250 | ✅ OK | Modal de autenticación rediseñado con control segmentado (Iniciar Sesión / Crear Cuenta), show/hide password, confirmación y tarjeta suiza sólida. |
| `src/components/TargetStoreSelector.tsx` | ~101 | ✅ OK | Selector visual de destino vectorial (PostgreSQL, MongoDB Atlas, Multi-Destino) con dots de estado. |

---

## 2. Inventario de Backend (`backend/app/`)

| Archivo | Líneas Aprox. | Límite (<800) | Responsabilidad Principal |
| :--- | :---: | :---: | :--- |
| `app/main.py` | ~125 | ✅ OK | Inicialización FastAPI, CORS, montaje de rutas (incluyendo `routes_chat`), lifespan y configuración de loop Windows. |
| `app/core/config.py` | ~67 | ✅ OK | Configuración con Pydantic Settings (.env) con soporte para DashScope Embeddings (batch_size=10, Singapur) y Qwen LLM (`qwen3.8-flash`, US Virginia). |
| `app/schemas/chat.py` | ~40 | ✅ OK | Schemas Pydantic para `ChatRequest`, `ChatResponse` (con `is_conversational`, `primary_source`, `primary_score`) y `CitationItem`. |
| `app/llm/llm_client.py` | ~79 | ✅ OK | Cliente HTTP async con httpx para el endpoint OpenAI-compatible de Qwen 3.8 Flash (`temperature=0.1`). |
| `app/llm/agent_service.py` | ~215 | ✅ OK | Orquestador RAG estricto: detección de saludos conversacionales, recuperación vectorial, cero alucinación y extracción de preguntas dinámicas desde chunks reales. |
| `app/api/routes_chat.py` | ~40 | ✅ OK | Endpoints `POST /api/chat` y `GET /api/chat/suggestions` protegidos por tenant. |
| `app/api/routes_ingest.py` | ~100 | ✅ OK | Endpoint `POST /api/ingest` de subida de archivos multipart con validación de extensión y tamaño. |
| `app/api/routes_drive.py` | ~90 | ✅ OK | Endpoint `POST /api/drive/ingest` para descarga e ingesta de documentos desde Google Drive. |
| `app/api/routes_search.py` | ~120 | ✅ OK | Endpoint `POST /api/search` de búsqueda vectorial semántica con cálculo de similitud coseno. |
| `app/api/routes_jobs.py` | ~80 | ✅ OK | Endpoints `GET /api/jobs/{id}` y SSE para monitoreo en tiempo real del progreso de ingestión. |
| `app/api/routes_knowledge.py` | ~120 | ✅ OK | Endpoints para listar, inspeccionar y borrar chunks de una sesión o usuario. |
| `app/api/routes_backup.py` | ~140 | ✅ OK | Generación de backup `.ragpkg` (JSONL + Gzip) y restauración en base vectorial. |
| `app/api/routes_auth.py` | ~295 | ✅ OK | Registro, login, emisión de API Keys y claim persistidos en PostgreSQL Neon relacional con fallback en memoria. |
| `app/api/routes_rag_api.py` | ~130 | ✅ OK | Endpoint público `POST /api/v1/rag/query` autenticado vía API Key para LLMs y agentes. |
| `app/chunking/semantic_chunker.py` | ~180 | ✅ OK | Algoritmo de *Semantic Chunking* adaptativo por oraciones y percentil de distancia coseno. |
| `app/embeddings/alibaba_dashscope.py` | ~117 | ✅ OK | Cliente API compatible con DashScope para `text-embedding-v3` (1024 dims) con límite de batch forzado a 10 items. |
| `app/embeddings/embedding_factory.py` | ~26 | ✅ OK | Factoría de embeddings: selector automático entre DashScope y Mock según configuración. |
| `app/core/user_db.py` | ~180 | ✅ OK | Repositorio relacional PostgreSQL Neon (`users` y `api_keys`) con claves foráneas, unicidad e integridad ACID. |
| `app/core/auth.py` | ~215 | ✅ OK | Multi-tenancy isolation (`TenantContext`), hashing de contraseñas (bcrypt), tokens JWT y API keys validados contra PostgreSQL. |
| `app/vector_stores/store_manager.py` | ~230 | ✅ OK | Enrutador y failover automático entre PostgreSQL y MongoDB Atlas. |
| `app/vector_stores/postgres_store.py` | ~210 | ✅ OK | Driver de PostgreSQL con extensión pgvector, índices HNSW y aislamiento multi-tenant. |
| `app/vector_stores/mongo_store.py` | ~275 | ✅ OK | Driver de MongoDB Atlas con soporte para índices vectoriales y cálculo coseno. |
| `app/pipeline/purge_worker.py` | ~90 | ✅ OK | Tarea periódica en segundo plano para depurar sesiones y chunks efímeros tras 24h. |

---

## 3. Estado de Infraestructura Validada

- **PostgreSQL Neon (Remoto):** ✅ Conectado y operativo (`ep-red-flower-aem6lhey-pooler...`). Alberga las tablas relacionales `users` y `api_keys` con integridad ACID, además de la extensión `pgvector`.
- **MongoDB Atlas (Remoto):** ✅ Conectado y operativo (`cluster0.vrzzkve.mongodb.net`, base `ragdb`). Chunks de `neurochat.txt` indexados y validados.
- **Embeddings Reales:** ✅ Alibaba Cloud DashScope `text-embedding-v3` (1024 dimensiones, batch size max 10) vía región Singapur (`dashscope-intl.aliyuncs.com`).
- **Generación LLM:** ✅ Alibaba Cloud Qwen `qwen3.8-flash` vía región US Virginia (`ws-lghtetahpb40cmex.us-east-1.maas.aliyuncs.com`).
- **Agente Cero Alucinación:** ✅ Probado e integrado: responde saludos con naturalidad, se niega a inventar datos fuera de documentos con disclaimer protector, y cita con exactitud datos reales de `neurochat.txt`.
