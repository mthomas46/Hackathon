"""Logging configuration for the Data Services Dashboard Service.

This module provides centralized logging setup following ecosystem patterns.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import structlog

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


def setup_logging(config) -> None:
    """Setup logging configuration."""
    # Handle both dict and Pydantic model inputs
    if hasattr(config, "level"):
        level_str = config.level
        enable_structlog = getattr(config, "enable_structlog", True)
        log_format = getattr(config, "format", "json")
    else:
        level_str = config.get("level", "INFO")
        enable_structlog = config.get("enable_structlog", True)
        log_format = config.get("format", "json")

    level = getattr(logging, level_str.upper())

    # Configure standard logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("dashboard.log", mode="a")],
    )

    # Configure structlog if available and enabled
    if STRUCTLOG_AVAILABLE and enable_structlog:
        import structlog

        # Configure structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                (
                    structlog.processors.JSONRenderer()
                    if log_format == "json"
                    else structlog.processors.ConsoleRenderer(colors=True)
                ),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    if STRUCTLOG_AVAILABLE:
        import structlog

        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


def get_dashboard_logger(name: str) -> logging.Logger:
    """Get a dashboard-specific logger."""
    return get_logger(f"data_dashboard.{name}")
