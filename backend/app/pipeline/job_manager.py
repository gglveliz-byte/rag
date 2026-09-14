"""In-memory job lifecycle management and SSE real-time event streaming."""

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncGenerator
from fastapi import HTTPException, status

from app.schemas.api_models import JobResponse, JobStatus


class JobManager:
    """Tracks asynchronous ingestion jobs and dispatches real-time SSE events."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, job_id: str, filename: str, tenant_id: str) -> JobResponse:
        """Register a new job in QUEUED state."""
        now = datetime.now(timezone.utc).isoformat()
        job_data: dict[str, Any] = {
            "job_id": job_id,
            "filename": filename,
            "tenant_id": tenant_id,
            "status": JobStatus.QUEUED,
            "progress": 0,
            "stage_message": "En cola de procesamiento",
            "created_at": now,
            "error": None,
        }
        async with self._lock:
            self._jobs[job_id] = job_data
            self._subscribers[job_id] = []

        return JobResponse(**job_data)

    async def update_progress(
        self,
        job_id: str,
        status: JobStatus,
        progress: int,
        stage_message: str,
        error: str | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> None:
        """Update job status and notify all listening SSE streams."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return

            job["status"] = status
            job["progress"] = progress
            job["stage_message"] = stage_message
            if error:
                job["error"] = error

            # Clone subscriber list to broadcast safely
            subscribers = list(self._subscribers.get(job_id, []))

        # Payload to stream
        payload = {
            "job_id": job_id,
            "status": status.value,
            "progress": progress,
            "stage_message": stage_message,
            "error": error,
            **(extra_data or {}),
        }

        for q in subscribers:
            try:
                q.put_nowait(payload)
            except Exception:
                pass

    async def subscribe(self, job_id: str) -> AsyncGenerator[dict[str, Any], None]:
        """Subscribe to a job's progress event queue for SSE."""
        q: asyncio.Queue = asyncio.Queue(maxsize=50)

        async with self._lock:
            if job_id not in self._jobs:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} no encontrado.",
                )
            self._subscribers.setdefault(job_id, []).append(q)
            current_job = dict(self._jobs[job_id])

        # Yield current initial state
        yield {
            "job_id": job_id,
            "status": current_job["status"].value if hasattr(current_job["status"], "value") else current_job["status"],
            "progress": current_job["progress"],
            "stage_message": current_job["stage_message"],
            "error": current_job.get("error"),
        }

        # If already completed or failed, terminate stream
        if current_job["status"] in (JobStatus.COMPLETED, JobStatus.FAILED):
            return

        try:
            while True:
                data = await q.get()
                yield data
                if data.get("status") in ("completed", "failed"):
                    break
        finally:
            async with self._lock:
                if job_id in self._subscribers and q in self._subscribers[job_id]:
                    self._subscribers[job_id].remove(q)

    def get_job(self, job_id: str) -> JobResponse | None:
        job = self._jobs.get(job_id)
        if not job:
            return None
        return JobResponse(**job)

    def list_jobs(self, tenant_id: str) -> list[JobResponse]:
        tenant_jobs = [
            JobResponse(**j) for j in self._jobs.values()
            if j.get("tenant_id") == tenant_id
        ]
        return sorted(tenant_jobs, key=lambda x: x.created_at, reverse=True)


# Global JobManager singleton
job_manager = JobManager()
