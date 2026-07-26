"""
Logging Configuration
Structured logging setup with JSON support
"""

import logging
import logging.config

from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging():
    """
    Configure application logging
    Uses JSON format for structured logging
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    if settings.LOG_FORMAT.lower() == "json":
        configure_json_logging(log_level)
    else:
        configure_standard_logging(log_level)


def configure_json_logging(log_level: int):
    """Configure JSON logging format"""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt=("%(timestamp)s %(level)s " "%(name)s %(message)s"),
        timestamp=True,
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def configure_standard_logging(log_level: int):
    """Configure standard logging format"""
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            },
        },
        "handlers": {
            "default": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": True,
            }
        },
    }
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    """
    return logging.getLogger(name)
