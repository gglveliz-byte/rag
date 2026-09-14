"""Job tracking and real-time SSE progress streaming routes."""

import json
from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.core.auth import TenantContext, get_tenant_context
from app.pipeline.job_manager import job_manager
from app.schemas.api_models import JobResponse

router = APIRouter(prefix="/jobs", tags=["Pipeline Jobs & Streaming"])


@router.get(
    "",
    response_model=list[JobResponse],
    summary="List all ingestion jobs for current tenant",
)
async def list_jobs(tenant: TenantContext = Depends(get_tenant_context)) -> list[JobResponse]:
    """Return all jobs associated with the current tenant/session."""
    return job_manager.list_jobs(tenant.tenant_id)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job status and progress details",
)
async def get_job_detail(job_id: str) -> JobResponse:
    """Retrieve details for a specific ingestion job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' no encontrado.",
        )
    return job


@router.get(
    "/{job_id}/stream",
    summary="Subscribe to real-time Server-Sent Events (SSE) for job progress",
)
async def stream_job_progress(job_id: str):
    """Open a persistent Server-Sent Events stream for real-time progress updates."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' no encontrado.",
        )

    async def event_generator():
        async for event_payload in job_manager.subscribe(job_id):
            yield {
                "event": "progress" if event_payload.get("status") not in ("completed", "failed") else event_payload.get("status"),
                "data": json.dumps(event_payload),
            }

    return EventSourceResponse(event_generator())
