import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from app.config import settings

WRITE_LOGS = settings.WRITE_LOGS

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_FILE = LOG_DIR / "rag_pipeline.log"
LOGGER_NAME = "sirius.rag"


def get_rag_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    # we only log to disk if running a dev instance locally
    if WRITE_LOGS:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
        return logger

    # else for prod on vercel, log to stdout instead
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
        return logger


def log_event(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    get_rag_logger().info(json.dumps(payload, default=str, ensure_ascii=True))
