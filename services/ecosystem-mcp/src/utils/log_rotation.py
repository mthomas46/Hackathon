"""
Log rotation configuration.

Provides rotating file handlers to prevent log files from growing indefinitely.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_log_rotation(
    log_file: Path | str,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    log_level: str = "INFO",
) -> logging.Handler:
    """
    Set up rotating file handler for logs.
    
    Args:
        log_file: Path to log file
        max_bytes: Maximum file size before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        log_level: Logging level
    
    Returns:
        Configured RotatingFileHandler
    
    Example:
        >>> handler = setup_log_rotation("server.log", max_bytes=10*1024*1024, backup_count=5)
        >>> logger.addHandler(handler)
    """
    handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8',
    )
    
    # Set formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Set level
    handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    return handler

