"""Google Drive public document download and ingestion trigger route."""

import asyncio
import uuid
from fastapi import APIRouter, Depends, status

from app.core.auth import TenantContext, get_tenant_context
from app.loaders.drive_downloader import download_drive_file
from app.pipeline.ingest_pipeline import run_ingestion_pipeline
from app.pipeline.job_manager import job_manager
from app.schemas.api_models import DriveIngestRequest, IngestResponse, JobStatus

router = APIRouter(prefix="/drive", tags=["Google Drive Ingestion"])


async def _download_and_ingest(
    job_id: str,
    url: str,
    tenant_id: str,
    is_ephemeral: bool,
    targets: list[str],
    tags: list[str],
    replace_if_exists: bool,
) -> None:
    """Download Google Drive file and chain into the ingestion pipeline."""
    try:
        await job_manager.update_progress(
            job_id=job_id,
            status=JobStatus.EXTRACTING,
            progress=5,
            stage_message="Conectando y descargando archivo desde Google Drive público...",
        )
        downloaded_path = await download_drive_file(url)
        filename = downloaded_path.name

        # Update filename in job
        job = job_manager.get_job(job_id)
        if job:
            job.filename = filename

        # Continue with standard pipeline
        await run_ingestion_pipeline(
            job_id=job_id,
            file_path=downloaded_path,
            original_filename=filename,
            tenant_id=tenant_id,
            is_ephemeral=is_ephemeral,
            targets=targets,
            tags=tags,
            replace_if_exists=replace_if_exists,
        )
    except Exception as exc:
        await job_manager.update_progress(
            job_id=job_id,
            status=JobStatus.FAILED,
            progress=0,
            stage_message=f"Error al descargar desde Google Drive: {exc}",
            error=str(exc),
        )


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest public Google Drive document via URL",
)
async def ingest_google_drive(
    payload: DriveIngestRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> IngestResponse:
    """Download and ingest a public Google Drive document without cloud credentials."""
    job_id = str(uuid.uuid4())

    await job_manager.create_job(
        job_id=job_id,
        filename="google_drive_file",
        tenant_id=tenant.tenant_id,
    )

    asyncio.create_task(
        _download_and_ingest(
            job_id=job_id,
            url=payload.url,
            tenant_id=tenant.tenant_id,
            is_ephemeral=tenant.is_ephemeral,
            targets=payload.targets or ["postgres"],
            tags=payload.tags,
            replace_if_exists=payload.replace_if_exists,
        )
    )

    return IngestResponse(
        job_id=job_id,
        status="queued",
        filename="Google Drive Link",
        message="Enlace de Google Drive recibido. Descarga e ingesta iniciada.",
    )
