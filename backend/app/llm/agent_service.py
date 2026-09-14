"""Strict Grounded RAG Agent service ensuring zero-hallucination factuality."""

import logging
import re
import time

from app.core.auth import TenantContext
from app.embeddings.embedding_factory import get_embedding_service
from app.llm.llm_client import qwen_client
from app.schemas.chat import ChatRequest, ChatResponse, CitationItem
from app.vector_stores.store_manager import store_manager

logger = logging.getLogger("rag_engine.agent_service")

SYSTEM_PROMPT = (
    "Eres un Asistente Inteligente Especializado en la base de conocimiento privada del usuario.\n\n"
    "PAUTAS FUNDAMENTALES DE RESPUESTA:\n"
    "1. PARAFRASEA CON NATURALIDAD Y FLUIDEZ: No copies bloques literales del texto. "
    "Explica los conceptos con tus propias palabras, de forma clara, ágil, conversacional y profesional.\n"
    "2. CERO ALUCINACIÓN (FIDELIDAD FACTUAL): Basa cada hecho, nombre propio, función o métrica estrictamente en los fragmentos de contexto provistos. "
    "No inventes datos que no figuren en la base de conocimiento.\n"
    "3. RESPUESTA ÁGIL Y DIRECTA AL GRANO: Responde directamente a lo que el usuario consulta, sin introducciones largas ni rodeos para mantener máxima velocidad y dinamismo.\n"
    "4. TONO: Cercano, humano, inteligente y en español."
)

GREETING_PATTERNS = [
    r"^(hola|buenas|buenos d[ií]as|buenas tardes|buenas noches|hey|hi|hello|saludos|qu[eé] tal)(\s+.*)?$",
    r"^(qui[eé]n eres|c[oó]mo te llamas|qu[eé] puedes hacer|qu[eé] eres|ayuda|help)$",
]



class GroundedRAGAgent:
    """Orchestrates semantic retrieval and zero-hallucination Qwen generation."""

    def _is_conversational_greeting(self, text: str) -> bool:
        """Check if query is purely a conversational greeting or intro."""
        clean = text.strip().lower()
        # Clean common trailing punctuation
        clean = re.sub(r"[¿?¡!.,;:]", "", clean).strip()
        for pat in GREETING_PATTERNS:
            if re.match(pat, clean):
                return True
        return False

    async def chat(self, request: ChatRequest, tenant: TenantContext) -> ChatResponse:
        """Process user question against isolated tenant memory and generate grounded answer."""
        start_time = time.perf_counter()
        query_text = request.query.strip()

        # 1. Natural handling for greetings & conversational pleasantries
        if self._is_conversational_greeting(query_text):
            greeting_messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres el Agente Inteligente Especializado en la base de conocimiento del usuario (RAG Knowledge Engine / NeuroChat). "
                        "El usuario te saluda o pregunta qué haces. Responde con calidez, naturalidad y cortesía en español, "
                        "presentándote y explicando que estás listo para responder consultas, explicar conceptos o analizar "
                        "cualquier tema contenido en sus documentos indexados."
                    ),
                },
                {"role": "user", "content": query_text},
            ]
            try:
                greeting_answer = await qwen_client.generate_response(messages=greeting_messages, temperature=0.7)
            except Exception:
                greeting_answer = (
                    "¡Hola! Soy tu Agente Especializado. Estoy aquí para responder cualquier pregunta o "
                    "analizar detalles basados estrictamente en tus documentos y base de conocimiento. ¿En qué puedo orientarte hoy?"
                )

            exec_time = round((time.perf_counter() - start_time) * 1000, 2)
            return ChatResponse(
                query=query_text,
                answer=greeting_answer,
                has_grounding=False,
                is_conversational=True,
                query_mode="precise",
                primary_source=None,
                primary_score=None,
                citations=[],
                total_citations=0,
                model=qwen_client._model,
                execution_time_ms=exec_time,
            )

        # 2. DUAL MODE HANDLING: Full Raw Document Inspection vs Precise Semantic Chunk Search
        if request.mode == "full":
            all_chunks = await store_manager.get_all_chunks(tenant.tenant_id)
            if not all_chunks:
                docs = await store_manager.get_all_documents(tenant.tenant_id)
                for d in docs:
                    d_chunks = await store_manager.get_document_chunks(tenant.tenant_id, d.document_id)
                    all_chunks.extend(d_chunks)

            if not all_chunks:
                exec_time = round((time.perf_counter() - start_time) * 1000, 2)
                return ChatResponse(
                    query=query_text,
                    answer="No hay documentos ni fragmentos indexados en tu base de conocimiento para consultar.",
                    has_grounding=False,
                    is_conversational=False,
                    query_mode="full",
                    primary_source=None,
                    primary_score=None,
                    citations=[],
                    total_citations=0,
                    model=qwen_client._model,
                    execution_time_ms=exec_time,
                )

            all_chunks.sort(key=lambda c: (c.document_id, c.chunk_index))
            docs = await store_manager.get_all_documents(tenant.tenant_id)
            doc_names = {d.document_id: d.filename for d in docs}

            context_blocks: list[str] = []
            citations: list[CitationItem] = []
            for ch in all_chunks:
                fname = doc_names.get(ch.document_id, "Documento")
                context_blocks.append(f"--- DOCUMENTO: {fname} (Fragmento {ch.chunk_index + 1}) ---\n{ch.content}")
                citations.append(
                    CitationItem(
                        chunk_id=ch.chunk_id,
                        filename=fname,
                        content=ch.content,
                        similarity_score=1.0,
                        chunk_index=ch.chunk_index,
                    )
                )

            primary_doc = citations[0].filename if citations else "Base de Conocimiento"
            full_raw_context = "\n\n".join(context_blocks)

            full_system_prompt = (
                "Eres un Agente Especializado con acceso a TODA LA INFORMACIÓN INTEGRAL (en bruto) de los documentos "
                "de la base de conocimiento privada del usuario.\n\n"
                "REGLAS:\n"
                "1. Analiza minuciosamente todo el contexto provisto para responder a la consulta del usuario.\n"
                "2. Si el usuario solicita un resumen, visión general, detalle específico o análisis comparativo, "
                "utiliza toda la información disponible en el texto de forma exhaustiva.\n"
                "3. No inventes información que no esté en el documento.\n"
                "4. Responde con lenguaje fluido, natural, profesional y en español."
            )

            messages = [
                {"role": "system", "content": full_system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"INFORMACIÓN INTEGRAL DE LA BASE DE CONOCIMIENTO (DOCUMENTO COMPLETO EN BRUTO):\n\n"
                        f"{full_raw_context}\n\n"
                        f"CONSULTA DEL USUARIO:\n{query_text}\n\n"
                        f"Instrucción: Sintetiza y responde con exactitud considerando la totalidad del documento provisto."
                    ),
                },
            ]

            try:
                answer_text = await qwen_client.generate_response(messages=messages, temperature=0.2, max_tokens=1500)
            except Exception as e:
                logger.warning("LLM call in full mode encountered an issue: %s", e)
                answer_text = (
                    "El análisis integral del documento tomó más tiempo del esperado por saturación temporal del proveedor. "
                    "Por favor, intenta nuevamente o consulta temas específicos con el modo 'Extracto Preciso'."
                )

            exec_time = round((time.perf_counter() - start_time) * 1000, 2)

            return ChatResponse(
                query=query_text,
                answer=answer_text,
                has_grounding=True,
                is_conversational=False,
                query_mode="full",
                primary_source=primary_doc,
                primary_score=100.0,
                citations=citations,
                total_citations=len(citations),
                model=qwen_client._model,
                execution_time_ms=exec_time,
            )

        # 3. PRECISE MODE: Vectorize query using Embeddings (1024 dims) and search top-k chunks
        embedder = get_embedding_service()
        query_embeddings = await embedder.embed([query_text])
        query_vec = query_embeddings[0]

        search_results = await store_manager.search(
            tenant_id=tenant.tenant_id,
            embedding=query_vec,
            top_k=request.top_k,
            store=request.store,
            threshold=request.score_threshold,
        )

        # 4. If no relevant chunks found in tenant documents, answer naturally with context awareness
        if not search_results:
            docs = await store_manager.get_all_documents(tenant.tenant_id)
            doc_names = [d.filename for d in docs] if docs else []
            doc_ctx = f"Tus documentos registrados son: {', '.join(doc_names)}." if doc_names else "Actualmente no tienes documentos subidos."

            natural_fallback_messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres el Asistente Inteligente Especializado en la base de conocimiento del usuario.\n"
                        f"Contexto de la cuenta: {doc_ctx}\n\n"
                        "El usuario ha realizado una pregunta o comentario cuya información NO figura en sus documentos indexados, "
                        "o es un tema externo (por ejemplo: talleres mecánicos, vehículos, recetas, o preguntas de por qué algo no está).\n\n"
                        "INSTRUCCIONES:\n"
                        "1. Responde con calidez humana, empatía, simpatía y naturalidad en español (NUNCA respondas como un contestador automático ni repitas frases acartonadas).\n"
                        "2. Explica con amabilidad que sobre ese tema puntual no tienes información cargada en su base de conocimiento.\n"
                        "3. Si viene al caso, menciona de qué temas tratan sus documentos y que con gusto aprenderás si sube un archivo sobre eso.\n"
                        "4. NO inventes datos factuales falsos sobre lo que no sabes. Sé breve, fresco y conversacional (1 o 2 párrafos cortos)."
                    ),
                },
                {"role": "user", "content": query_text},
            ]

            try:
                fallback_answer = await qwen_client.generate_response(messages=natural_fallback_messages, temperature=0.6, max_tokens=350)
            except Exception:
                fallback_answer = (
                    "No tengo información sobre ese tema en tus documentos actuales. "
                    "Mi memoria está enfocada en los archivos que has subido a tu base de conocimiento."
                )

            exec_time = round((time.perf_counter() - start_time) * 1000, 2)
            return ChatResponse(
                query=query_text,
                answer=fallback_answer,
                has_grounding=False,
                is_conversational=False,
                query_mode="precise",
                primary_source=None,
                primary_score=None,
                citations=[],
                total_citations=0,
                model=qwen_client._model,
                execution_time_ms=exec_time,
            )

        # 5. Prepare structured context block and citation metadata
        context_blocks: list[str] = []
        citations: list[CitationItem] = []

        for idx, res in enumerate(search_results, start=1):
            doc_name = res.source_file or "Documento"
            chunk_idx = res.metadata.get("chunk_index", 0) if res.metadata else 0
            pct_score = round(res.score * 100, 1)

            context_blocks.append(
                f"--- FRAGMENTO {idx} (Fuente: {doc_name}, Similitud: {pct_score}%) ---\n{res.content}"
            )

            citations.append(
                CitationItem(
                    chunk_id=res.chunk_id,
                    filename=doc_name,
                    content=res.content,
                    similarity_score=round(res.score, 4),
                    chunk_index=chunk_idx,
                )
            )

        full_context_str = "\n\n".join(context_blocks)
        top_match = search_results[0]
        primary_source = top_match.source_file or "Documento"
        primary_score = round(top_match.score * 100, 1)

        # 6. Construct grounded prompt for LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"FRAGMENTOS DE CONTEXTO DE LA BASE DE CONOCIMIENTO:\n\n"
                    f"{full_context_str}\n\n"
                    f"PREGUNTA DEL USUARIO:\n{query_text}\n\n"
                    f"Instrucción: Responde parafraseando de forma natural, ágil y al grano basándote únicamente en los hechos provistos. "
                    f"Explica con tus palabras sin copiar bloques textuales literales."
                ),
            },
        ]

        # 7. Invoke LLM with moderate temperature (0.4) for natural paraphrase and quick max_tokens
        try:
            answer_text = await qwen_client.generate_response(messages=messages, temperature=0.4, max_tokens=750)
        except Exception as e:
            logger.warning("LLM call in precise mode encountered an issue: %s", e)
            answer_text = "Hubo una interrupción temporal al conectar con el motor de generación. Por favor, reintenta tu consulta en unos momentos."

        exec_time = round((time.perf_counter() - start_time) * 1000, 2)

        return ChatResponse(
            query=query_text,
            answer=answer_text,
            has_grounding=True,
            is_conversational=False,
            query_mode="precise",
            primary_source=primary_source,
            primary_score=primary_score,
            citations=citations,
            total_citations=len(citations),
            model=qwen_client._model,
            execution_time_ms=exec_time,
        )

    async def get_suggested_prompts(self, tenant: TenantContext) -> list[str]:
        """Extract dynamic questions based on real ingested documents in knowledge base."""
        all_chunks = await store_manager.get_all_chunks(tenant.tenant_id)
        if not all_chunks:
            return [
                "¿Qué temas aborda mi base de conocimiento?",
                "¿Cuáles son los puntos clave de mis documentos?",
                "¿Qué información general está registrada?",
            ]

        prompts: list[str] = []
        for c in all_chunks:
            headers = re.findall(r"(?:^|\n)#{1,4}\s*([^\n]+)", c.content)
            for h in headers:
                clean_h = re.sub(r"^\d+[\.\d*]*\s*", "", h).strip()
                clean_h = re.sub(r"^[—\-\*\s]+", "", clean_h).strip()
                if (
                    clean_h
                    and len(clean_h) > 5
                    and not clean_h.startswith("---")
                    and "base de conocimiento" not in clean_h.lower()
                ):
                    if not clean_h.startswith("¿"):
                        clean_h = f"¿Qué detalles hay sobre {clean_h}?"
                    if clean_h not in prompts:
                        prompts.append(clean_h)
                        if len(prompts) >= 4:
                            return prompts

        if not prompts:
            docs = await store_manager.get_all_documents(tenant.tenant_id)
            for doc in docs[:4]:
                prompts.append(f"¿Qué información contiene el archivo {doc.filename}?")

        return prompts[:4]


rag_agent = GroundedRAGAgent()

