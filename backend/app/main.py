"""FastAPI main application entrypoint for RAG Knowledge Engine."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    routes_auth,
    routes_backup,
    routes_chat,
    routes_drive,
    routes_ingest,
    routes_jobs,
    routes_knowledge,
    routes_rag_api,
    routes_search,
)
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.pipeline.purge_worker import start_purge_worker, stop_purge_worker
from app.schemas.api_models import HealthStatus
from app.vector_stores.store_manager import store_manager

settings = get_settings()
logger = setup_logging(debug=settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan event handler."""
    logger.info("Starting up %s...", settings.PROJECT_NAME)

    # 1. Ensure storage directories exist
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Storage directories initialized: %s", settings.STORAGE_DIR)

    # 2. Asynchronously initialize vector databases and user tables (non-blocking)
    from app.core.user_db import user_db
    asyncio.create_task(store_manager.initialize())
    asyncio.create_task(user_db.initialize())

    # 3. Start periodic purge worker for expired 24h ephemeral sessions
    start_purge_worker(interval_seconds=3600)

    yield

    # Shutdown
    stop_purge_worker()
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Ingestion & Vector Memory Engine with Dual-Lifecycle & LLM Retrieval API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware configuration
cors_origins = settings.cors_origins_list
if "*" in cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register API Routers
app.include_router(routes_auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_rag_api.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_ingest.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_drive.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_jobs.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_search.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_knowledge.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_backup.router, prefix=settings.API_V1_PREFIX)


@app.get(
    f"{settings.API_V1_PREFIX}/health",
    response_model=HealthStatus,
    tags=["System"],
    summary="Check health and connectivity status",
)
async def health_check() -> HealthStatus:
    """Verify system status, database availability and DashScope configuration."""
    pg_ok, mg_ok = await store_manager.get_health()
    dashscope_configured = bool(settings.DASHSCOPE_API_KEY and settings.DASHSCOPE_API_KEY.strip())

    return HealthStatus(
        status="healthy" if (pg_ok or mg_ok or settings.USE_MOCK_EMBEDDINGS) else "degraded",
        postgres_connected=pg_ok,
        mongo_connected=mg_ok,
        dashscope_configured=dashscope_configured,
        mock_mode=settings.USE_MOCK_EMBEDDINGS or not dashscope_configured,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/", tags=["System"])
async def root():
    """Root endpoint providing service information."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "engine": settings.PROJECT_NAME,
            "status": "online",
            "version": "1.0.0",
            "docs": "/docs",
        },
    )
