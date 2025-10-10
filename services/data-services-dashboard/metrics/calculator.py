"""
Metric calculation and aggregation.

Calculates aggregate metrics from log entries for dashboard display.
"""

from typing import List, Dict
from data.models import LogEntry, MetricsSummary


def calculate_metrics(logs: List[LogEntry]) -> MetricsSummary:
    """
    Calculate aggregate metrics from log entries.
    
    Args:
        logs: List of parsed log entries
        
    Returns:
        MetricsSummary with calculated statistics
        
    Example:
        metrics = calculate_metrics(logs)
        print(f"Total: {metrics.total_operations}")
        print(f"Error rate: {metrics.error_rate}%")
    """
    if not logs:
        return MetricsSummary()
    
    # Count operations
    total = len(logs)
    successful = sum(1 for log in logs if log.success is True)
    failed = sum(1 for log in logs if log.success is False)
    
    # Calculate error rate
    error_rate = (failed / total * 100) if total > 0 else 0.0
    
    # Calculate average duration
    durations = [log.duration_ms for log in logs if log.duration_ms is not None]
    avg_duration = sum(durations) / len(durations) if durations else 0.0
    
    # Count operations per service
    operations_per_service = calculate_operations_per_service(logs)
    
    return MetricsSummary(
        total_operations=total,
        successful_operations=successful,
        failed_operations=failed,
        avg_duration_ms=avg_duration,
        error_rate=error_rate,
        operations_per_service=operations_per_service
    )


def aggregate_by_service(logs: List[LogEntry]) -> Dict[str, MetricsSummary]:
    """
    Calculate metrics for each service separately.
    
    Args:
        logs: List of parsed log entries
        
    Returns:
        Dictionary mapping service name to MetricsSummary
        
    Example:
        metrics_by_service = aggregate_by_service(logs)
        for service, metrics in metrics_by_service.items():
            print(f"{service}: {metrics.total_operations} operations")
    """
    # Group logs by service
    logs_by_service: Dict[str, List[LogEntry]] = {}
    for log in logs:
        if log.service not in logs_by_service:
            logs_by_service[log.service] = []
        logs_by_service[log.service].append(log)
    
    # Calculate metrics for each service
    metrics_by_service = {}
    for service, service_logs in logs_by_service.items():
        metrics_by_service[service] = calculate_metrics(service_logs)
    
    return metrics_by_service


def calculate_error_rate(logs: List[LogEntry]) -> float:
    """
    Calculate error rate as a percentage.
    
    Args:
        logs: List of parsed log entries
        
    Returns:
        Error rate between 0.0 and 100.0
        
    Example:
        error_rate = calculate_error_rate(logs)
        print(f"Error rate: {error_rate:.1f}%")
    """
    if not logs:
        return 0.0
    
    failed = sum(1 for log in logs if log.success is False)
    total = len(logs)
    
    return (failed / total * 100) if total > 0 else 0.0


def calculate_avg_duration(logs: List[LogEntry]) -> float:
    """
    Calculate average operation duration in milliseconds.
    
    Args:
        logs: List of parsed log entries
        
    Returns:
        Average duration in milliseconds
        
    Example:
        avg_duration = calculate_avg_duration(logs)
        print(f"Average: {avg_duration:.2f}ms")
    """
    durations = [log.duration_ms for log in logs if log.duration_ms is not None]
    
    if not durations:
        return 0.0
    
    return sum(durations) / len(durations)


def calculate_operations_per_service(logs: List[LogEntry]) -> Dict[str, int]:
    """
    Count operations per service.
    
    Args:
        logs: List of parsed log entries
        
    Returns:
        Dictionary mapping service name to operation count
        
    Example:
        ops_per_service = calculate_operations_per_service(logs)
        # {"doc_store": 50, "prompt_store": 30, "memory-agent": 20}
    """
    operations_per_service: Dict[str, int] = {}
    
    for log in logs:
        service = log.service
        operations_per_service[service] = operations_per_service.get(service, 0) + 1
    
    return operations_per_service


def calculate_operations_per_type(logs: List[LogEntry]) -> Dict[str, int]:
    """
    Count operations per operation type.
    
    Args:
        logs: List of parsed log entries
        
    Returns:
        Dictionary mapping operation type to count
        
    Example:
        ops_per_type = calculate_operations_per_type(logs)
        # {"CREATE": 30, "READ": 50, "UPDATE": 10, "DELETE": 10}
    """
    operations_per_type: Dict[str, int] = {}
    
    for log in logs:
        op_type = log.operation_type
        operations_per_type[op_type] = operations_per_type.get(op_type, 0) + 1
    
    return operations_per_type


def calculate_status_code_distribution(logs: List[LogEntry]) -> Dict[int, int]:
    """
    Count operations by HTTP status code.
    
    Args:
        logs: List of parsed log entries
        
    Returns:
        Dictionary mapping status code to count
        
    Example:
        status_distribution = calculate_status_code_distribution(logs)
        # {200: 80, 201: 15, 404: 3, 500: 2}
    """
    status_distribution: Dict[int, int] = {}
    
    for log in logs:
        if log.status_code is not None:
            status_distribution[log.status_code] = status_distribution.get(log.status_code, 0) + 1
    
    return status_distribution


def calculate_percentile(values: List[float], percentile: int) -> float:
    """
    Calculate a percentile value from a list of numbers.
    
    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)
        
    Returns:
        Percentile value
        
    Example:
        durations = [10, 20, 30, 40, 50]
        p95 = calculate_percentile(durations, 95)  # 47.5
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    index = (percentile / 100) * (len(sorted_values) - 1)
    
    if index.is_integer():
        return sorted_values[int(index)]
    else:
        lower = sorted_values[int(index)]
        upper = sorted_values[int(index) + 1]
        fraction = index - int(index)
        return lower + (upper - lower) * fraction


def calculate_duration_percentiles(logs: List[LogEntry]) -> Dict[str, float]:
    """
    Calculate duration percentiles (p50, p95, p99).
    
    Args:
        logs: List of parsed log entries
        
    Returns:
        Dictionary with p50, p95, p99 durations
        
    Example:
        percentiles = calculate_duration_percentiles(logs)
        # {"p50": 12.5, "p95": 45.2, "p99": 78.9}
    """
    durations = [log.duration_ms for log in logs if log.duration_ms is not None]
    
    if not durations:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
    
    return {
        "p50": calculate_percentile(durations, 50),
        "p95": calculate_percentile(durations, 95),
        "p99": calculate_percentile(durations, 99)
    }


def calculate_min_max_duration(logs: List[LogEntry]) -> Dict[str, float]:
    """
    Calculate min and max durations.
    
    Args:
        logs: List of parsed log entries
        
    Returns:
        Dictionary with min and max durations
        
    Example:
        min_max = calculate_min_max_duration(logs)
        # {"min": 2.5, "max": 150.7}
    """
    durations = [log.duration_ms for log in logs if log.duration_ms is not None]
    
    if not durations:
        return {"min": 0.0, "max": 0.0}
    
    return {
        "min": min(durations),
        "max": max(durations)
    }

