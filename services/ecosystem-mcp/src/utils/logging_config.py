"""
Comprehensive logging configuration for Ecosystem MCP Service.

Provides structured logging with multiple outputs and rich terminal feedback.
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

import structlog
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ..config import settings


# Global console for rich output
console = Console()


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_rich: bool = True
) -> None:
    """
    Setup comprehensive logging system.
    
    Features:
    - Structured logging (structlog)
    - Rich terminal output
    - File logging
    - JSON format for machines
    - Human-readable format for console
    
    Args:
        log_level: Logging level (default from settings)
        log_file: Optional log file path
        enable_rich: Enable rich terminal output
    """
    log_level = log_level or settings.log_level
    
    # Create logs directory
    logs_dir = Path("./logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure standard logging
    logging.basicConfig(
        level=log_level.upper(),
        format="%(message)s",
        handlers=[],
    )
    
    # Add rich handler for beautiful terminal output
    if enable_rich:
        rich_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            markup=True,
            show_time=True,
            show_level=True,
            show_path=True,
        )
        rich_handler.setLevel(log_level.upper())
        logging.root.addHandler(rich_handler)
    else:
        # Simple console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level.upper())
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logging.root.addHandler(console_handler)
    
    # Add file handler (JSON format for structured logs)
    if log_file:
        log_path = logs_dir / log_file
    else:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_path = logs_dir / f"ecosystem-mcp-{timestamp}.log"
    
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)  # Capture everything in file
    file_handler.setFormatter(
        logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    )
    logging.root.addHandler(file_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"[bold green]Logging initialized[/bold green]")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log file: {log_path}")


def log_operation_start(operation: str, details: Optional[dict] = None) -> None:
    """
    Log the start of a major operation.
    
    Args:
        operation: Operation name
        details: Optional operation details
    """
    logger = logging.getLogger(__name__)
    console.rule(f"[bold blue]Starting: {operation}[/bold blue]")
    
    if details:
        logger.info(f"Operation: {operation}")
        for key, value in details.items():
            logger.info(f"  {key}: {value}")
    else:
        logger.info(f"Starting operation: {operation}")


def log_operation_complete(
    operation: str,
    duration_seconds: Optional[float] = None,
    results: Optional[dict] = None
) -> None:
    """
    Log the completion of a major operation.
    
    Args:
        operation: Operation name
        duration_seconds: Optional operation duration
        results: Optional operation results
    """
    logger = logging.getLogger(__name__)
    
    if duration_seconds:
        console.rule(
            f"[bold green]✅ Completed: {operation} "
            f"({duration_seconds:.2f}s)[/bold green]"
        )
    else:
        console.rule(f"[bold green]✅ Completed: {operation}[/bold green]")
    
    if results:
        logger.info(f"Operation completed: {operation}")
        for key, value in results.items():
            logger.info(f"  {key}: {value}")


def log_operation_failed(
    operation: str,
    error: Exception,
    details: Optional[dict] = None
) -> None:
    """
    Log a failed operation.
    
    Args:
        operation: Operation name
        error: Exception that occurred
        details: Optional error details
    """
    logger = logging.getLogger(__name__)
    console.rule(f"[bold red]❌ Failed: {operation}[/bold red]")
    
    logger.error(f"Operation failed: {operation}")
    logger.error(f"Error: {error}", exc_info=True)
    
    if details:
        for key, value in details.items():
            logger.error(f"  {key}: {value}")


def create_progress() -> Progress:
    """
    Create a Rich progress bar for long-running operations.
    
    Returns:
        Configured Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=False,
    )


def log_metric(metric_name: str, value: float, unit: Optional[str] = None) -> None:
    """
    Log a metric value.
    
    Args:
        metric_name: Metric name
        value: Metric value
        unit: Optional unit
    """
    logger = logging.getLogger(__name__)
    
    if unit:
        logger.info(f"📊 {metric_name}: {value:.2f} {unit}")
    else:
        logger.info(f"📊 {metric_name}: {value}")


def log_checkpoint(checkpoint: str, details: Optional[dict] = None) -> None:
    """
    Log a checkpoint in a long-running process.
    
    Args:
        checkpoint: Checkpoint name
        details: Optional checkpoint details
    """
    logger = logging.getLogger(__name__)
    console.print(f"[bold cyan]🔹 Checkpoint: {checkpoint}[/bold cyan]")
    
    if details:
        for key, value in details.items():
            logger.info(f"  {key}: {value}")


class OperationLogger:
    """
    Context manager for logging operations with automatic success/failure tracking.
    
    Usage:
        with OperationLogger("Ingesting documents") as op:
            # Do work
            op.checkpoint("Parsed 100 files")
            op.metric("files_processed", 100)
            # Automatically logs success on exit
    """
    
    def __init__(self, operation: str, details: Optional[dict] = None):
        """Initialize operation logger."""
        self.operation = operation
        self.details = details
        self.start_time = None
        self.checkpoints = []
        self.metrics = {}
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        """Start operation logging."""
        self.start_time = datetime.now()
        log_operation_start(self.operation, self.details)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete operation logging."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            # Success
            results = {
                "duration_seconds": duration,
                **self.metrics
            }
            log_operation_complete(self.operation, duration, results)
        else:
            # Failure
            log_operation_failed(self.operation, exc_val, self.details)
        
        return False  # Don't suppress exception
    
    def checkpoint(self, checkpoint: str, details: Optional[dict] = None):
        """Log a checkpoint."""
        self.checkpoints.append(checkpoint)
        log_checkpoint(checkpoint, details)
    
    def metric(self, name: str, value: float, unit: Optional[str] = None):
        """Log a metric."""
        self.metrics[name] = value
        log_metric(name, value, unit)
    
    def progress(self, message: str):
        """Log progress message."""
        self.logger.info(f"⏳ {message}")

