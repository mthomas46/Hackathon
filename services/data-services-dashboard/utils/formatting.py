"""
Formatting utilities for dashboard display.

Provides functions for formatting durations, timestamps, workflow IDs, etc.
"""

from datetime import datetime, timezone
from typing import Optional


def format_duration(duration_ms: Optional[float]) -> str:
    """
    Format duration in human-readable form.
    
    Args:
        duration_ms: Duration in milliseconds
        
    Returns:
        Formatted duration string
        
    Example:
        >>> format_duration(150.5)
        "150.5ms"
        >>> format_duration(1500.0)
        "1.50s"
        >>> format_duration(None)
        "N/A"
    """
    if duration_ms is None:
        return "N/A"
    
    if duration_ms == 0:
        return "0ms"
    
    if duration_ms < 1000:
        return f"{duration_ms:.1f}ms"
    elif duration_ms < 60000:
        return f"{duration_ms / 1000:.2f}s"
    else:
        minutes = int(duration_ms / 60000)
        seconds = (duration_ms % 60000) / 1000
        return f"{minutes}m {seconds:.1f}s"


def truncate_workflow_id(workflow_id: Optional[str], max_length: int = 12) -> str:
    """
    Truncate workflow ID for display.
    
    Args:
        workflow_id: Workflow ID string
        max_length: Maximum length (default: 12)
        
    Returns:
        Truncated workflow ID
        
    Example:
        >>> truncate_workflow_id("workflow_abc123_def456_xyz789")
        "workflow_abc..."
        >>> truncate_workflow_id(None)
        "N/A"
    """
    if not workflow_id:
        return "N/A"
    
    if len(workflow_id) <= max_length:
        return workflow_id
    
    return f"{workflow_id[:max_length-3]}..."


def format_timestamp(dt: datetime) -> str:
    """
    Format timestamp for display.
    
    Args:
        dt: Datetime object
        
    Returns:
        Formatted timestamp string
        
    Example:
        >>> format_timestamp(datetime(2025, 10, 9, 12, 30, 45))
        "2025-10-09 12:30:45"
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format percentage for display.
    
    Args:
        value: Percentage value (0-100)
        decimals: Number of decimal places (default: 1)
        
    Returns:
        Formatted percentage string
        
    Example:
        >>> format_percentage(12.5)
        "12.5%"
        >>> format_percentage(0.0)
        "0.0%"
    """
    return f"{value:.{decimals}f}%"


def format_service_name(service: str) -> str:
    """
    Format service name for display (capitalize, replace dashes).
    
    Args:
        service: Service name
        
    Returns:
        Formatted service name
        
    Example:
        >>> format_service_name("doc_store")
        "Doc Store"
        >>> format_service_name("external-service-store")
        "External Service Store"
    """
    # Replace underscores and dashes with spaces
    formatted = service.replace("_", " ").replace("-", " ")
    # Capitalize each word
    return formatted.title()


def format_status_code(status_code: Optional[int]) -> str:
    """
    Format HTTP status code with emoji indicator.
    
    Args:
        status_code: HTTP status code
        
    Returns:
        Formatted status code with emoji
        
    Example:
        >>> format_status_code(200)
        "✅ 200"
        >>> format_status_code(404)
        "❌ 404"
    """
    if status_code is None:
        return "N/A"
    
    if status_code < 400:
        return f"✅ {status_code}"
    else:
        return f"❌ {status_code}"


def format_count(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    Format count with singular/plural form.
    
    Args:
        count: Count value
        singular: Singular form
        plural: Plural form (default: singular + "s")
        
    Returns:
        Formatted count string
        
    Example:
        >>> format_count(1, "operation")
        "1 operation"
        >>> format_count(5, "operation")
        "5 operations"
    """
    if plural is None:
        plural = f"{singular}s"
    
    return f"{count} {singular if count == 1 else plural}"


def format_uptime(uptime_seconds: float) -> str:
    """
    Format uptime in human-readable form.
    
    Args:
        uptime_seconds: Uptime in seconds
        
    Returns:
        Formatted uptime string
        
    Example:
        >>> format_uptime(65)
        "1m 5s"
        >>> format_uptime(3665)
        "1h 1m 5s"
    """
    if uptime_seconds < 60:
        return f"{int(uptime_seconds)}s"
    
    minutes = int(uptime_seconds / 60)
    seconds = int(uptime_seconds % 60)
    
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    
    hours = int(minutes / 60)
    minutes = minutes % 60
    
    if hours < 24:
        return f"{hours}h {minutes}m"
    
    days = int(hours / 24)
    hours = hours % 24
    
    return f"{days}d {hours}h"

