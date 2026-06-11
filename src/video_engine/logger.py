"""Logging helpers for the video engine."""

from __future__ import annotations

import logging

LOGGER_NAME = "theia.video_engine"


def configure_logger(level: int = logging.INFO) -> logging.Logger:
    """Configure and return the shared application logger.

    The logger is configured once with a stream handler and a compact
    formatter. Repeated calls reuse the same logger instance without adding
    duplicate handlers.
    """

    logger = logging.getLogger(LOGGER_NAME)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)

    logger.setLevel(level)
    logger.propagate = False
    return logger


logger = configure_logger()