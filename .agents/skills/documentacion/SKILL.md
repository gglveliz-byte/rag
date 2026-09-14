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
| `src/vite-env.d.ts` | ~11 | ✅ OK | Declaración de tipos TypeScript para variables de entorno de Vite (`VITE_API_URL`). |
| `src/App.tsx` | ~430 | ✅ OK | Estado central de navegación, autenticación, monitor SSE acotado a pestañas de subida (`upload`/`drive`) con cierre `onClose` para evitar fugas entre vistas. |
| `src/index.css` | ~685 | ✅ OK | Variables de diseño, reset, navegación móvil/desktop (`.mobile-tab-nav`, `.sidebar`), modales, y animación fluida de tipeo para el bot. |
| `src/landing.css` | ~180 | ✅ OK | Estilos de la Landing Page: responsividad móvil/desktop, dock flotante inferior y protección contra copiado/arrastre. |
| `src/types/index.ts` | ~132 | ✅ OK | Definiciones TypeScript: documentos, chunks con `embedding` opcional, salud del sistema, modos de consulta (`mode`, `query_mode`) y payload de chat. |
| `src/services/api.ts` | ~215 | ✅ OK | Cliente Axios con interceptor multi-tenant y baseURL configurable por `VITE_API_URL` para despliegue desacoplado en producción. |
| `src/services/sse.ts` | ~77 | ✅ OK | Cliente EventSource SSE con soporte de `VITE_API_URL` para monitoreo en tiempo real de ingestión. |
| `src/components/LandingPage.tsx` | ~85 | ✅ OK | Vista inicial responsiva: versión panorámica para desktop y vertical para móvil, imagen protegida e inerte, botones exclusivos de interacción. |
| `src/components/AgentChat.tsx` | ~669 | ✅ OK | Chat de Agente IA con selector HUD de modo (`🎯 Extractos Precisos` vs `📚 Toda la Base`), parafraseo natural sin demoras de pensamiento, respuestas empáticas contextualizadas para temas no indexados, y sanitización defensiva de preguntas sugeridas puras sin párrafos. |
| `src/components/PipelineMonitor.tsx` | ~206 | ✅ OK | Monitor SSE de ingesta con botón de cierre `(x)`, etapas de alto contraste y consola terminal oscura para eventos en tiempo real. |
| `src/components/FileUploader.tsx` | ~170 | ✅ OK | Panel de subida de archivos locales con autoselección inteligente de la base conectada (MongoDB Atlas / PostgreSQL). |
| `src/components/DriveImporter.tsx` | ~130 | ✅ OK | Importador de archivos públicos de Google Drive con autoselección de base conectada. |
| `src/components/SearchPanel.tsx` | ~190 | ✅ OK | Panel de consulta vectorial semántica con slider de umbral, top-k y autoselección de base activa. |
| `src/components/KnowledgeExplorer.tsx` | ~268 | ✅ OK | Explorador interactivo de documentos y chunks con conteo visible de fragmentos, badges de vectores densos (1024 dims), preview numérico y visor terminal del vector completo. |
| `src/components/BackupManager.tsx` | ~140 | ✅ OK | Panel de exportación e importación de paquetes `.ragpkg` agnósticos. |
| `src/components/ApiKeysManager.tsx` | ~310 | ✅ OK | Panel rediseñado de API Keys con terminal estilo macOS, URL backend 100% dinámica, tabs de lenguaje (cURL, Python, JS), copiado y gestión de claves. |
| `src/components/AuthModal.tsx` | ~250 | ✅ OK | Modal de autenticación rediseñado con control segmentado (Iniciar Sesión / Crear Cuenta), show/hide password, confirmación y tarjeta suiza sólida. |
| `src/components/TargetStoreSelector.tsx` | ~101 | ✅ OK | Selector visual de destino vectorial (PostgreSQL, MongoDB Atlas, Multi-Destino) con dots de estado. |

---

## 2. Inventario de Backend (`backend/app/`)

| Archivo | Líneas Aprox. | Límite (<800) | Responsabilidad Principal |
| :--- | :---: | :---: | :--- |
| `run.py` | ~33 | ✅ OK | Lanzador de entrada agnóstico: soporte para Linux/Render con lectura de `$PORT` y `$HOST`, y WindowsSelectorEventLoopPolicy para Windows. |
| `app/main.py` | ~135 | ✅ OK | Inicialización FastAPI, CORS con soporte wildcard regex y lista explícita, montaje de rutas, lifespan y configuración de loop. |
| `app/core/config.py` | ~67 | ✅ OK | Configuración con Pydantic Settings (.env) con soporte para DashScope Embeddings (batch_size=10, Singapur) y Qwen LLM (`qwen3.8-flash`, US Virginia). |
| `app/schemas/chat.py` | ~45 | ✅ OK | Schemas Pydantic para `ChatRequest` (con campo `mode`), `ChatResponse` (con `query_mode`, `is_conversational`, `primary_source`) y `CitationItem`. |
| `app/llm/llm_client.py` | ~97 | ✅ OK | Cliente HTTP async con httpx (timeout extendido a 90s) para el endpoint OpenAI-compatible de Qwen 3.8 Flash. |
| `app/llm/agent_service.py` | ~377 | ✅ OK | Orquestador RAG dual con parafraseo ágil y natural, generador de preguntas sugeridas dinámicas y puras (sin respuestas ni párrafos incrustados), respuesta empática contextualizada para temas no indexados y modos `precise` y `full`. |
| `app/api/routes_chat.py` | ~41 | ✅ OK | Endpoints `POST /api/chat` y `GET /api/chat/suggestions` protegidos por tenant. |
| `app/api/routes_ingest.py` | ~100 | ✅ OK | Endpoint `POST /api/ingest` de subida de archivos multipart con validación de extensión y tamaño. |
| `app/api/routes_drive.py` | ~90 | ✅ OK | Endpoint `POST /api/drive/ingest` para descarga e ingesta de documentos desde Google Drive. |
| `app/api/routes_search.py` | ~120 | ✅ OK | Endpoint `POST /api/search` de búsqueda vectorial semántica con cálculo de similitud coseno. |
| `app/api/routes_jobs.py` | ~80 | ✅ OK | Endpoints `GET /api/jobs/{id}` y SSE para monitoreo en tiempo real del progreso de ingestión. |
| `app/api/routes_knowledge.py` | ~120 | ✅ OK | Endpoints para listar, inspeccionar y borrar chunks de una sesión o usuario con retorno de embeddings. |
| `app/api/routes_backup.py` | ~140 | ✅ OK | Generación de backup `.ragpkg` (JSONL + Gzip) y restauración en base vectorial. |
| `app/api/routes_auth.py` | ~295 | ✅ OK | Registro, login, emisión de API Keys y claim persistidos en PostgreSQL Neon relacional con fallback en memoria. |
| `app/api/routes_rag_api.py` | ~130 | ✅ OK | Endpoint público `POST /api/v1/rag/query` autenticado vía API Key para LLMs y agentes. |
| `app/chunking/semantic_chunker.py` | ~180 | ✅ OK | Algoritmo de *Semantic Chunking* adaptativo por oraciones y percentil de distancia coseno. |
| `app/embeddings/alibaba_dashscope.py` | ~117 | ✅ OK | Cliente API compatible con DashScope para `text-embedding-v3` (1024 dims) con límite de batch forzado a 10 items. |
| `app/embeddings/embedding_factory.py` | ~26 | ✅ OK | Factoría de embeddings: selector automático entre DashScope y Mock según configuración. |
| `app/core/user_db.py` | ~180 | ✅ OK | Repositorio relacional PostgreSQL Neon (`users` y `api_keys`) con claves foráneas, unicidad e integridad ACID. |
| `app/core/auth.py` | ~215 | ✅ OK | Multi-tenancy isolation (`TenantContext`), hashing de contraseñas (bcrypt), tokens JWT y API keys validados contra PostgreSQL. |
| `app/vector_stores/store_manager.py` | ~245 | ✅ OK | Enrutador y failover automático entre PostgreSQL y MongoDB Atlas ante respuestas vacías o caídas. |
| `app/vector_stores/postgres_store.py` | ~399 | ✅ OK | Driver de PostgreSQL con pgvector: conversión segura de `Vector` a lista (`.to_list()`), soporte de índices y aislamiento multi-tenant. |
| `app/vector_stores/mongo_store.py` | ~275 | ✅ OK | Driver de MongoDB Atlas con soporte para índices vectoriales y cálculo coseno. |
| `app/pipeline/purge_worker.py` | ~90 | ✅ OK | Tarea periódica en segundo plano para depurar sesiones y chunks efímeros tras 24h. |

---

## 3. Estado de Infraestructura Validada

- **PostgreSQL Neon (Remoto):** ✅ Conectado y operativo (`ep-red-flower-aem6lhey-pooler...`). Alberga las tablas relacionales `users` y `api_keys` con integridad ACID, además de la extensión `pgvector`.
- **MongoDB Atlas (Remoto):** ✅ Conectado y operativo (`cluster0.vrzzkve.mongodb.net`, base `ragdb`). Chunks de `neurochat.txt` indexados y validados.
- **Embeddings Reales:** ✅ Alibaba Cloud DashScope `text-embedding-v3` (1024 dimensiones, batch size max 10) vía región Singapur (`dashscope-intl.aliyuncs.com`).
- **Generación LLM:** ✅ Alibaba Cloud Qwen `qwen3.8-flash` vía región US Virginia (`ws-lghtetahpb40cmex.us-east-1.maas.aliyuncs.com`).
- **Modos de Consulta Dual:**
  - **Extracto Preciso:** Recupera los top-k fragmentos más cercanos por similitud coseno con badge de coincidencia semántica.
  - **Toda la Base (Completo en Bruto):** Extrae la totalidad de fragmentos registrados del documento en bruto y genera un análisis exhaustivo/panorámico con badge de consulta integral.
