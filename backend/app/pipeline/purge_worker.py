"""Periodic background worker for purging ephemeral 24-hour guest knowledge bases."""

import asyncio
import logging

from app.core.config import get_settings
from app.vector_stores.store_manager import store_manager

logger = logging.getLogger("rag_engine.purge_worker")
settings = get_settings()

_purge_task: asyncio.Task | None = None
_running: bool = False


async def _purge_loop(interval_seconds: int = 3600) -> None:
    """Infinite loop executing periodic purge of expired guest documents."""
    logger.info("Purge worker started. Checking expired ephemeral documents every %ds.", interval_seconds)
    while _running:
        try:
            purged_count = await store_manager.purge_expired()
            if purged_count > 0:
                logger.info("Purge worker removed %d expired ephemeral documents from vector stores.", purged_count)
        except Exception as exc:
            logger.warning("Error during ephemeral purge execution: %s", exc)

        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break


def start_purge_worker(interval_seconds: int = 3600) -> None:
    """Start background purge loop."""
    global _purge_task, _running
    if _purge_task is None or _purge_task.done():
        _running = True
        _purge_task = asyncio.create_task(_purge_loop(interval_seconds))


def stop_purge_worker() -> None:
    """Gracefully cancel and stop purge loop."""
    global _purge_task, _running
    _running = False
    if _purge_task and not _purge_task.done():
        _purge_task.cancel()
