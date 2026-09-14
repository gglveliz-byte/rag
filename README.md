# Knowledge Engine — Memoria Vectorial y Recuperación Contextual para LLMs

Motor empresarial modular, escalable y desacoplado para ingesta documental inteligente, particionamiento semántico (*Semantic Chunking*) y persistencia vectorial en **PostgreSQL (pgvector)** y **MongoDB**, con ciclo de vida dual (Modo Invitado 24h y Modo Cuenta Persistente con API Keys) y exposición de API para LLMs externas.

---

## Características Principales

### 1. Ciclo de Vida Dual (Sandbox 24h vs Cuenta Persistente)
- **Modo Invitado (Sandbox Efímero):** Ingesta inmediata y prueba de búsqueda vectorial sin registro. Los datos tienen un TTL de 24 horas y se depuran automáticamente mediante un worker periódico en segundo plano.
- **Respaldos Agnósticos (`.ragpkg`):** Cualquier usuario invitado puede descargar su base de conocimiento completa en formato `.ragpkg` (JSONL + Gzip) para utilizarla en su propia infraestructura.
- **Reclamo de Sesión (*Claim Session*):** Si el usuario se registra o inicia sesión, puede vincular su espacio de trabajo efímero con un solo clic, convirtiendo sus documentos en permanentes sin volver a subir ni vectorizar nada.
- **API Keys para LLMs de Terceros:** Generación de claves `rke_live_...` para consultar la memoria vectorial desde LangChain, LlamaIndex, OpenAI Custom GPTs o agentes autónomos vía `POST /api/v1/rag/query`.

### 2. Ingesta y Loaders Especializados
- **Archivos Locales:** Soporte nativo para PDF (PyMuPDF con seguimiento de páginas), Word (`.docx`), Excel (`.xlsx` con preservación tabular semántica), CSV y Texto plano/Markdown.
- **Google Drive Público:** Descarga e ingesta automatizada sin necesidad de API de Google Cloud mediante `gdown` y streaming directo.
- **Deduplicación por SHA-256:** Evita duplicados en memoria vectorial antes de procesar texto, con opción de reemplazo bajo demanda.

### 3. Semantic Chunking Inteligente
- Segmentación por proposiciones y oraciones.
- Análisis de transiciones temáticas mediante distancia coseno y cálculo de umbral por percentil.
- Límites dinámicos de tokens mínimos y máximos para chunks semánticamente cohesivos.
- Compatible con **Alibaba DashScope** (`text-embedding-v3`) y modo mock para desarrollo local sin costo.

### 4. Almacenamiento Vectorial Multi-Destino
- **PostgreSQL (`pgvector`):** Índices HNSW para búsquedas sub-lineales, operadores de distancia coseno `<=>` y aislamiento estricto por `tenant_id`.
- **MongoDB (Vector Search):** Colecciones flexibles con motor híbrido y fallback de similitud en memoria.
- **Store Manager:** Enrutador con failover automático y capacidad de persistencia multi-destino simultánea.

### 5. Interfaz de Usuario de Ingeniería
- Diseñada con CSS puro bajo principios de *Swiss Precision* y estética HUD técnica.
- Transmisión de progreso en tiempo real mediante **Server-Sent Events (SSE)**.
- Explorador interactivo de chunks y metadatos.
- Herramienta para copiar contexto formateado listo para inyectar en prompts de LLMs.

---

## Requisitos Previos

- **Python 3.12+**
- **Node.js 18+** y npm
- **Docker** y Docker Compose (opcional, para PostgreSQL y MongoDB locales)

---

## Instalación y Puesta en Marcha

### 1. Iniciar Bases de Datos (Docker)

```bash
docker-compose up -d
```

Levantará:
- PostgreSQL con extensión `pgvector` en el puerto `5432` (`ragdb`)
- MongoDB 7 en el puerto `27017` (`ragdb`)

### 2. Configurar y Ejecutar el Backend

```bash
cd backend
python -m venv .venv
# En Windows:
.\.venv\Scripts\activate
# En Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env

uvicorn app.main:app --reload --port 8000
```

- Documentación interactiva Swagger: `http://localhost:8000/docs`
- Verificación de estado: `http://localhost:8000/api/health`

### 3. Configurar y Ejecutar el Frontend

```bash
cd frontend
npm install
npm run dev
```

- Interfaz web: `http://localhost:5173`

---

## Ejemplo de Consulta desde LLMs Externas (API RAG)

```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Authorization: Bearer rke_live_TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Cuáles son las condiciones de garantía?",
    "top_k": 5,
    "score_threshold": 0.7
  }'
```

**Respuesta recibida:**
```json
{
  "query": "¿Cuáles son las condiciones de garantía?",
  "results_count": 2,
  "context_text": "[Fuente: garantia.pdf (Pág. 3) | Similitud: 0.92]:\nLa garantía cubre defectos de fábrica...",
  "chunks": [
    {
      "chunk_id": "...",
      "content": "La garantía cubre defectos de fábrica...",
      "similarity_score": 0.92,
      "source_file": "garantia.pdf",
      "metadata": { "page_number": 3 }
    }
  ],
  "execution_time_ms": 42.1
}
```

---

## Reglas de Arquitectura y Desarrollo

- **Límite de 800 líneas por archivo:** Todos los módulos respetan la modularidad estricta.
- **Documentación Viva:** El registro completo de componentes se mantiene actualizado en la skill `.agents/skills/documentacion/SKILL.md`.
