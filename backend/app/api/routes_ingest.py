"""Multipart local document upload and ingestion trigger route."""

import asyncio
import uuid
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status

from app.core.auth import TenantContext, get_tenant_context
from app.core.config import get_settings
from app.core.security import sanitize_filename, validate_file_extension
from app.pipeline.ingest_pipeline import run_ingestion_pipeline
from app.pipeline.job_manager import job_manager
from app.schemas.api_models import IngestResponse

router = APIRouter(prefix="/ingest", tags=["Document Ingestion"])
settings = get_settings()


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload local document and start async ingestion pipeline",
)
async def ingest_file(
    file: UploadFile,
    targets: str = Form("postgres", description="Comma-separated stores: postgres, mongo, both"),
    tags: str = Form("", description="Comma-separated tags"),
    replace_if_exists: bool = Form(False, description="Replace existing document if hash matches"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> IngestResponse:
    """Accept multipart document file upload and spawn background ingestion pipeline."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de archivo inválido.",
        )

    # Validate file extension
    validate_file_extension(file.filename)
    safe_name = sanitize_filename(file.filename)

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save to disk
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    temp_save_path = settings.UPLOAD_DIR / f"{job_id}_{safe_name}"

    try:
        content = await file.read()
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"El archivo supera el límite máximo permitido de {settings.MAX_FILE_SIZE_MB}MB.",
            )

        with open(temp_save_path, "wb") as f:
            f.write(content)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar archivo en disco: {exc}",
        )

    # Parse targets and tags
    target_list = [t.strip().lower() for t in targets.split(",") if t.strip()]
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Register job
    await job_manager.create_job(
        job_id=job_id,
        filename=safe_name,
        tenant_id=tenant.tenant_id,
    )

    # Fire and forget async ingestion pipeline
    asyncio.create_task(
        run_ingestion_pipeline(
            job_id=job_id,
            file_path=temp_save_path,
            original_filename=safe_name,
            tenant_id=tenant.tenant_id,
            is_ephemeral=tenant.is_ephemeral,
            targets=target_list or ["postgres"],
            tags=tag_list,
            replace_if_exists=replace_if_exists,
        )
    )

    return IngestResponse(
        job_id=job_id,
        status="queued",
        filename=safe_name,
        message="Documento recibido. Pipeline de ingesta iniciado en segundo plano.",
    )
