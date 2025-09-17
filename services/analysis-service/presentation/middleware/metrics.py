"""Metrics middleware for monitoring API performance and usage."""

import time
import psutil
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ...shared.logging import fire_and_forget


class MetricsCollector:
    """Collector for API metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self.request_count = 0
        self.request_duration = 0.0
        self.error_count = 0
        self.endpoint_metrics: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()

    def record_request(self, method: str, path: str, duration: float, status_code: int):
        """Record request metrics."""
        self.request_count += 1
        self.request_duration += duration

        if status_code >= 400:
            self.error_count += 1

        # Record endpoint-specific metrics
        endpoint_key = f"{method}:{path}"
        if endpoint_key not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint_key] = {
                'count': 0,
                'total_duration': 0.0,
                'error_count': 0,
                'min_duration': float('inf'),
                'max_duration': 0.0
            }

        metrics = self.endpoint_metrics[endpoint_key]
        metrics['count'] += 1
        metrics['total_duration'] += duration
        metrics['min_duration'] = min(metrics['min_duration'], duration)
        metrics['max_duration'] = max(metrics['max_duration'], duration)

        if status_code >= 400:
            metrics['error_count'] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        uptime = time.time() - self.start_time
        avg_duration = self.request_duration / max(1, self.request_count)

        return {
            'uptime_seconds': uptime,
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'average_request_duration': avg_duration,
            'error_rate': self.error_count / max(1, self.request_count),
            'requests_per_second': self.request_count / max(1, uptime),
            'endpoint_metrics': self.endpoint_metrics
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_mb': psutil.virtual_memory().used / 1024 / 1024,
            'memory_available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections())
        }


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API metrics."""

    def __init__(self, app, metrics_collector: Optional[MetricsCollector] = None):
        """Initialize metrics middleware."""
        super().__init__(app)
        self.metrics = metrics_collector or MetricsCollector()

        # Endpoints to exclude from metrics
        self.exclude_paths = [
            '/health',
            '/metrics',
            '/favicon.ico'
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and collect metrics."""
        # Skip metrics for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)

            # Record successful request metrics
            duration = time.time() - start_time
            self.metrics.record_request(
                request.method,
                request.url.path,
                duration,
                response.status_code
            )

            # Add metrics headers
            response.headers['X-Response-Time'] = f"{duration:.3f}s"

            return response

        except Exception as exc:
            # Record error metrics
            duration = time.time() - start_time
            self.metrics.record_request(
                request.method,
                request.url.path,
                duration,
                500  # Internal server error
            )

            # Re-raise the exception
            raise

    def get_metrics_collector(self) -> MetricsCollector:
        """Get the metrics collector instance."""
        return self.metrics


class PrometheusMetricsExporter:
    """Exporter for Prometheus metrics format."""

    def __init__(self, metrics_collector: MetricsCollector, service_name: str = "analysis-service"):
        """Initialize Prometheus exporter."""
        self.metrics = metrics_collector
        self.service_name = service_name

    def export_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        # Request metrics
        summary = self.metrics.get_summary()
        lines.extend([
            f"# HELP {self.service_name}_requests_total Total number of requests",
            f"# TYPE {self.service_name}_requests_total counter",
            f"{self.service_name}_requests_total {summary['total_requests']}",
            "",
            f"# HELP {self.service_name}_requests_duration_seconds Total request duration",
            f"# TYPE {self.service_name}_requests_duration_seconds counter",
            f"{self.service_name}_requests_duration_seconds {summary['request_duration']}",
            "",
            f"# HELP {self.service_name}_requests_average_duration_seconds Average request duration",
            f"# TYPE {self.service_name}_requests_average_duration_seconds gauge",
            f"{self.service_name}_requests_average_duration_seconds {summary['average_request_duration']}",
            "",
            f"# HELP {self.service_name}_errors_total Total number of errors",
            f"# TYPE {self.service_name}_errors_total counter",
            f"{self.service_name}_errors_total {summary['total_errors']}",
            "",
            f"# HELP {self.service_name}_uptime_seconds Service uptime",
            f"# TYPE {self.service_name}_uptime_seconds gauge",
            f"{self.service_name}_uptime_seconds {summary['uptime_seconds']}",
        ])

        # Endpoint-specific metrics
        for endpoint, metrics in summary['endpoint_metrics'].items():
            method, path = endpoint.split(':', 1)
            safe_name = path.replace('/', '_').replace('-', '_').strip('_')

            lines.extend([
                "",
                f"# HELP {self.service_name}_endpoint_{safe_name}_requests_total Requests for {endpoint}",
                f"# TYPE {self.service_name}_endpoint_{safe_name}_requests_total counter",
                f"{self.service_name}_endpoint_{safe_name}_requests_total{{method=\"{method}\"}} {metrics['count']}",
                "",
                f"# HELP {self.service_name}_endpoint_{safe_name}_duration_seconds_total Total duration for {endpoint}",
                f"# TYPE {self.service_name}_endpoint_{safe_name}_duration_seconds_total counter",
                f"{self.service_name}_endpoint_{safe_name}_duration_seconds_total{{method=\"{method}\"}} {metrics['total_duration']}",
            ])

        # System metrics
        system_metrics = self.metrics.get_system_metrics()
        lines.extend([
            "",
            f"# HELP {self.service_name}_cpu_percent CPU usage percentage",
            f"# TYPE {self.service_name}_cpu_percent gauge",
            f"{self.service_name}_cpu_percent {system_metrics['cpu_percent']}",
            "",
            f"# HELP {self.service_name}_memory_percent Memory usage percentage",
            f"# TYPE {self.service_name}_memory_percent gauge",
            f"{self.service_name}_memory_percent {system_metrics['memory_percent']}",
            "",
            f"# HELP {self.service_name}_memory_used_mb Memory used in MB",
            f"# TYPE {self.service_name}_memory_used_mb gauge",
            f"{self.service_name}_memory_used_mb {system_metrics['memory_used_mb']}",
        ])

        return '\n'.join(lines)


class MetricsEndpoint:
    """FastAPI endpoint for exposing metrics."""

    def __init__(self, metrics_middleware: MetricsMiddleware):
        """Initialize metrics endpoint."""
        self.middleware = metrics_middleware
        self.exporter = PrometheusMetricsExporter(
            self.middleware.get_metrics_collector()
        )

    async def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return self.exporter.export_metrics()

    async def get_metrics_json(self) -> Dict[str, Any]:
        """Get metrics as JSON."""
        collector = self.middleware.get_metrics_collector()
        return {
            'summary': collector.get_summary(),
            'system': collector.get_system_metrics()
        }


# Global metrics instances
metrics_collector = MetricsCollector()
metrics_exporter = PrometheusMetricsExporter(metrics_collector)
metrics_endpoint = MetricsEndpoint(None)  # Will be set when middleware is created
