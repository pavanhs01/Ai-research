import logging
import sys

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Configure root logger with structured, environment-aware output."""
    log_level = logging.DEBUG if not settings.is_production else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    # Quiet noisy third-party loggers in production
    for noisy in ("httpx", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING if settings.is_production else logging.INFO)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
