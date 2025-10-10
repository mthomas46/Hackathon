"""
Log parsing and validation.

Parses raw log dictionaries into validated LogEntry models.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any
from pydantic import ValidationError

from .models import LogEntry
from utils.logging_client import dashboard_logger


def parse_log_entry(log: Dict[str, Any]) -> LogEntry:
    """
    Parse a raw log dictionary into a validated LogEntry.
    
    Args:
        log: Raw log dictionary from log-collector
        
    Returns:
        Validated LogEntry model
        
    Raises:
        ValidationError: If log fails validation
        
    Example:
        raw_log = {"timestamp": "2025-10-09T12:00:00Z", "service": "doc_store", ...}
        log_entry = parse_log_entry(raw_log)
        print(log_entry.service)  # Type-safe access
    """
    try:
        # Extract context (nested object)
        context = log.get("context", {})
        
        # Build LogEntry with defaults for missing fields
        log_entry = LogEntry(
            timestamp=datetime.fromisoformat(
                log.get("timestamp", datetime.now(timezone.utc).isoformat())
            ),
            service=log.get("service", "unknown"),
            level=log.get("level", "INFO"),
            message=log.get("message", ""),
            
            # From context
            operation_type=context.get("operation_type", "unknown"),
            method=context.get("method", ""),
            path=context.get("path", ""),
            status_code=context.get("status_code"),
            duration_ms=context.get("duration_ms"),
            success=context.get("success"),
            phase=context.get("phase", ""),
            workflow_id=context.get("workflow_id", "")
        )
        
        return log_entry
        
    except ValidationError as e:
        # Log validation error
        log_id = log.get("id", log.get("timestamp", "unknown"))
        dashboard_logger.validation_error("log_entry", log_id, str(e))
        raise
        
    except Exception as e:
        # Log parsing error
        log_id = log.get("id", log.get("timestamp", "unknown"))
        dashboard_logger.parsing_error(log_id, str(e))
        raise


def parse_logs(raw_logs: List[Dict[str, Any]]) -> List[LogEntry]:
    """
    Parse a list of raw logs into validated LogEntry models.
    
    Skips logs that fail validation rather than failing completely.
    
    Args:
        raw_logs: List of raw log dictionaries
        
    Returns:
        List of validated LogEntry models (may be shorter than input if some fail)
        
    Example:
        raw_logs = fetch_logs()
        log_entries = parse_logs(raw_logs)
        print(f"Parsed {len(log_entries)} logs")
    """
    parsed_logs = []
    failed_count = 0
    
    for raw_log in raw_logs:
        try:
            log_entry = parse_log_entry(raw_log)
            parsed_logs.append(log_entry)
        except (ValidationError, Exception):
            # Skip invalid logs (already logged in parse_log_entry)
            failed_count += 1
            continue
    
    # Log summary if there were failures
    if failed_count > 0:
        dashboard_logger.warning(
            f"Skipped {failed_count} invalid logs during parsing",
            total=len(raw_logs),
            parsed=len(parsed_logs),
            failed=failed_count
        )
    
    return parsed_logs


def validate_log(log: Dict[str, Any]) -> bool:
    """
    Validate that a log dictionary has required fields.
    
    Lightweight validation before full parsing.
    
    Args:
        log: Raw log dictionary
        
    Returns:
        True if log has required fields, False otherwise
        
    Example:
        if validate_log(raw_log):
            log_entry = parse_log_entry(raw_log)
    """
    # Required fields
    required_fields = ["timestamp", "service", "level"]
    
    # Check all required fields exist
    for field in required_fields:
        if field not in log:
            return False
    
    # Check types
    if not isinstance(log.get("timestamp"), str):
        return False
    if not isinstance(log.get("service"), str):
        return False
    if not isinstance(log.get("level"), str):
        return False
    
    # Check service name is not empty
    if not log.get("service"):
        return False
    
    return True


def filter_logs_by_phase(logs: List[LogEntry], phase: str = "complete") -> List[LogEntry]:
    """
    Filter logs by operation phase.
    
    Args:
        logs: List of log entries
        phase: Phase to filter by (default: "complete")
        
    Returns:
        Filtered list of log entries
        
    Example:
        completed_logs = filter_logs_by_phase(logs, "complete")
        print(f"{len(completed_logs)} completed operations")
    """
    return [log for log in logs if log.phase == phase]


def filter_logs_by_success(logs: List[LogEntry], success: bool) -> List[LogEntry]:
    """
    Filter logs by success status.
    
    Args:
        logs: List of log entries
        success: True for successful, False for failed
        
    Returns:
        Filtered list of log entries
        
    Example:
        successful_logs = filter_logs_by_success(logs, True)
        failed_logs = filter_logs_by_success(logs, False)
    """
    return [log for log in logs if log.success == success]


def filter_logs_by_service(logs: List[LogEntry], service: str) -> List[LogEntry]:
    """
    Filter logs by service name.
    
    Args:
        logs: List of log entries
        service: Service name to filter by
        
    Returns:
        Filtered list of log entries
        
    Example:
        doc_store_logs = filter_logs_by_service(logs, "doc_store")
    """
    return [log for log in logs if log.service == service]


def get_unique_services(logs: List[LogEntry]) -> List[str]:
    """
    Get list of unique service names from logs.
    
    Args:
        logs: List of log entries
        
    Returns:
        Sorted list of unique service names
        
    Example:
        services = get_unique_services(logs)
        # ["doc_store", "memory-agent", "prompt_store"]
    """
    services = set(log.service for log in logs)
    return sorted(list(services))


def get_unique_workflows(logs: List[LogEntry]) -> List[str]:
    """
    Get list of unique workflow IDs from logs.
    
    Args:
        logs: List of log entries
        
    Returns:
        Sorted list of unique workflow IDs (excluding empty strings)
        
    Example:
        workflows = get_unique_workflows(logs)
        # ["wf_abc123", "wf_def456", "wf_xyz789"]
    """
    workflows = set(log.workflow_id for log in logs if log.workflow_id)
    return sorted(list(workflows))

