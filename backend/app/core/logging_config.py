"""Structured logging configuration for RAG Knowledge Engine."""

import logging
import sys


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configure structured console logging for the application.

    Args:
        debug: If True, set level to DEBUG, otherwise INFO.

    Returns:
        Root application logger.
    """
    level = logging.DEBUG if debug else logging.INFO
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger("rag_engine")
    logger.setLevel(level)
    return logger
