"""
Shared metrics collection for LLM Documentation Ecosystem services.
Provides Prometheus-compatible metrics for monitoring and observability.
"""

from typing import Dict, Any, Optional
import time
import psutil
import os
from prometheus_client import (
    Counter, Histogram, Gauge, CollectorRegistry,
    generate_latest, CONTENT_TYPE_LATEST
)
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse


class ServiceMetrics:
    """Metrics collector for individual services."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.registry = CollectorRegistry()

        # HTTP request metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )

        # Business logic metrics
        self.document_processing_total = Counter(
            'document_processing_total',
            'Total number of documents processed',
            ['source_type', 'status'],
            registry=self.registry
        )

        self.analysis_operations_total = Counter(
            'analysis_operations_total',
            'Total number of analysis operations',
            ['operation_type', 'status'],
            registry=self.registry
        )

        # Error metrics
        self.errors_total = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type', 'endpoint'],
            registry=self.registry
        )

        # Resource metrics
        self.memory_usage_bytes = Gauge(
            'memory_usage_bytes',
            'Current memory usage in bytes',
            registry=self.registry
        )

        self.cpu_usage_percent = Gauge(
            'cpu_usage_percent',
            'Current CPU usage percentage',
            registry=self.registry
        )

        # Queue metrics
        self.queue_length = Gauge(
            'queue_length',
            'Current queue length',
            ['queue_name'],
            registry=self.registry
        )

        # Cache metrics
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total number of cache hits',
            ['cache_name'],
            registry=self.registry
        )

        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total number of cache misses',
            ['cache_name'],
            registry=self.registry
        )

        # External service metrics
        self.external_requests_total = Counter(
            'external_requests_total',
            'Total number of requests to external services',
            ['service_name', 'method', 'status'],
            registry=self.registry
        )

        self.external_request_duration_seconds = Histogram(
            'external_request_duration_seconds',
            'External request duration in seconds',
            ['service_name', 'method'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
            registry=self.registry
        )

        # Architecture Digitizer specific metrics
        self.architecture_digitizer_requests_total = Counter(
            'architecture_digitizer_requests_total',
            'Total number of architecture digitizer requests',
            ['system', 'status'],
            registry=self.registry
        )

        self.architecture_digitizer_request_duration_seconds = Histogram(
            'architecture_digitizer_request_duration_seconds',
            'Architecture digitizer request duration in seconds',
            ['system'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
            registry=self.registry
        )

        self.architecture_digitizer_api_failures_total = Counter(
            'architecture_digitizer_api_failures_total',
            'Total number of architecture digitizer API failures',
            ['system', 'error_type'],
            registry=self.registry
        )

        self.architecture_digitizer_cache_hits_total = Counter(
            'architecture_digitizer_cache_hits_total',
            'Total number of architecture digitizer cache hits',
            registry=self.registry
        )

        self.architecture_digitizer_cache_misses_total = Counter(
            'architecture_digitizer_cache_misses_total',
            'Total number of architecture digitizer cache misses',
            registry=self.registry
        )

        # Architecture Digitizer file upload metrics
        self.architecture_digitizer_file_uploads_total = Counter(
            'architecture_digitizer_file_uploads_total',
            'Total number of architecture digitizer file uploads',
            ['system', 'file_format', 'status'],
            registry=self.registry
        )

        self.architecture_digitizer_file_upload_duration_seconds = Histogram(
            'architecture_digitizer_file_upload_duration_seconds',
            'Architecture digitizer file upload duration in seconds',
            ['system', 'file_format'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
            registry=self.registry
        )

        self.architecture_digitizer_file_size_bytes = Histogram(
            'architecture_digitizer_file_size_bytes',
            'Size of uploaded files in bytes',
            ['system', 'file_format'],
            buckets=(1024, 10240, 102400, 1048576, 10485760),  # 1KB, 10KB, 100KB, 1MB, 10MB
            registry=self.registry
        )

    def update_resource_metrics(self):
        """Update system resource metrics."""
        try:
            process = psutil.Process(os.getpid())
            self.memory_usage_bytes.set(process.memory_info().rss)
            self.cpu_usage_percent.set(process.cpu_percent(interval=1))
        except Exception:
            # Silently ignore errors in metrics collection
            pass

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        self.update_resource_metrics()
        return generate_latest(self.registry).decode('utf-8')


# Global metrics instance
_service_metrics: Optional[ServiceMetrics] = None


def get_service_metrics(service_name: str) -> ServiceMetrics:
    """Get or create service metrics instance."""
    global _service_metrics
    if _service_metrics is None:
        _service_metrics = ServiceMetrics(service_name)
    return _service_metrics


def metrics_endpoint(service_name: str):
    """FastAPI endpoint for exposing metrics."""
    metrics = get_service_metrics(service_name)

    async def metrics_handler():
        """Return Prometheus metrics."""
        return PlainTextResponse(
            content=metrics.get_metrics(),
            media_type=CONTENT_TYPE_LATEST
        )

    return metrics_handler


def instrument_http_request(metrics: ServiceMetrics):
    """Middleware to instrument HTTP requests."""

    async def middleware(request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
            status = str(response.status_code)
        except Exception as e:
            # Record error
            metrics.errors_total.labels(
                error_type=type(e).__name__,
                endpoint=request.url.path
            ).inc()
            raise
        finally:
            # Record request metrics
            duration = time.time() - start_time
            metrics.http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status if 'status' in locals() else '500'
            ).inc()

            metrics.http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

        return response

    return middleware


# Convenience functions for business logic metrics
def record_document_processing(metrics: ServiceMetrics, source_type: str, status: str = 'success'):
    """Record document processing metrics."""
    metrics.document_processing_total.labels(
        source_type=source_type,
        status=status
    ).inc()


def record_analysis_operation(metrics: ServiceMetrics, operation_type: str, status: str = 'success'):
    """Record analysis operation metrics."""
    metrics.analysis_operations_total.labels(
        operation_type=operation_type,
        status=status
    ).inc()


def record_external_request(metrics: ServiceMetrics, service_name: str, method: str, status: str, duration: float):
    """Record external service request metrics."""
    metrics.external_requests_total.labels(
        service_name=service_name,
        method=method,
        status=status
    ).inc()

    metrics.external_request_duration_seconds.labels(
        service_name=service_name,
        method=method
    ).observe(duration)


def record_cache_operation(metrics: ServiceMetrics, cache_name: str, hit: bool):
    """Record cache operation metrics."""
    if hit:
        metrics.cache_hits_total.labels(cache_name=cache_name).inc()
    else:
        metrics.cache_misses_total.labels(cache_name=cache_name).inc()


def update_queue_length(metrics: ServiceMetrics, queue_name: str, length: int):
    """Update queue length metrics."""
    metrics.queue_length.labels(queue_name=queue_name).set(length)


# Architecture Digitizer specific metric functions
def record_architecture_digitizer_request(metrics: ServiceMetrics, system: str, status: str = 'success', duration: float = None):
    """Record architecture digitizer request metrics."""
    metrics.architecture_digitizer_requests_total.labels(
        system=system,
        status=status
    ).inc()

    if duration is not None:
        metrics.architecture_digitizer_request_duration_seconds.labels(
            system=system
        ).observe(duration)


def record_architecture_digitizer_api_failure(metrics: ServiceMetrics, system: str, error_type: str):
    """Record architecture digitizer API failure metrics."""
    metrics.architecture_digitizer_api_failures_total.labels(
        system=system,
        error_type=error_type
    ).inc()


def record_architecture_digitizer_cache(metrics: ServiceMetrics, hit: bool):
    """Record architecture digitizer cache metrics."""
    if hit:
        metrics.architecture_digitizer_cache_hits_total.inc()
    else:
        metrics.architecture_digitizer_cache_misses_total.inc()


def record_architecture_digitizer_file_upload(metrics: ServiceMetrics, system: str, file_format: str, file_size: int, status: str = 'success', duration: float = None):
    """Record architecture digitizer file upload metrics."""
    metrics.architecture_digitizer_file_uploads_total.labels(
        system=system,
        file_format=file_format,
        status=status
    ).inc()

    if duration is not None:
        metrics.architecture_digitizer_file_upload_duration_seconds.labels(
            system=system,
            file_format=file_format
        ).observe(duration)

    # Record file size regardless of status
    metrics.architecture_digitizer_file_size_bytes.labels(
        system=system,
        file_format=file_format
    ).observe(file_size)
