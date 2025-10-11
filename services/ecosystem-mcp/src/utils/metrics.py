"""
Prometheus metrics for the ecosystem-mcp service.

Tracks:
- Request duration and counts
- Error rates
- Database queries
- Embedding generations
- Cache operations
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time


# ============================================================================
# HTTP Metrics
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)


# ============================================================================
# Database Metrics
# ============================================================================

db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

db_connection_pool_available = Gauge(
    'db_connection_pool_available',
    'Available database connections'
)


# ============================================================================
# Embedding Metrics
# ============================================================================

embeddings_generated_total = Counter(
    'embeddings_generated_total',
    'Total embeddings generated',
    ['model']
)

embedding_generation_duration_seconds = Histogram(
    'embedding_generation_duration_seconds',
    'Embedding generation duration in seconds',
    ['model']
)

embedding_generation_errors_total = Counter(
    'embedding_generation_errors_total',
    'Total embedding generation errors',
    ['model', 'error_type']
)


# ============================================================================
# Search Metrics
# ============================================================================

search_requests_total = Counter(
    'search_requests_total',
    'Total search requests',
    ['status']
)

search_duration_seconds = Histogram(
    'search_duration_seconds',
    'Search request duration in seconds'
)

search_results_count = Histogram(
    'search_results_count',
    'Number of results returned per search'
)


# ============================================================================
# Ingestion Metrics
# ============================================================================

ingestion_jobs_total = Counter(
    'ingestion_jobs_total',
    'Total ingestion jobs',
    ['mode', 'status']
)

ingestion_documents_total = Counter(
    'ingestion_documents_total',
    'Total documents ingested',
    ['status']
)

ingestion_duration_seconds = Histogram(
    'ingestion_duration_seconds',
    'Ingestion job duration in seconds',
    ['mode']
)


# ============================================================================
# Cache Metrics
# ============================================================================

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)


# ============================================================================
# System Metrics
# ============================================================================

service_info = Gauge(
    'service_info',
    'Service information',
    ['version', 'environment']
)

service_up = Gauge(
    'service_up',
    'Service up status (1 = up, 0 = down)'
)


# ============================================================================
# Helper Functions
# ============================================================================

def track_http_request(method: str, endpoint: str, status: int, duration: float):
    """Track HTTP request metrics."""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_db_query(operation: str, table: str, duration: float):
    """Track database query metrics."""
    db_queries_total.labels(operation=operation, table=table).inc()
    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)


def track_embedding_generation(model: str, duration: float, success: bool = True, error_type: str = None):
    """Track embedding generation metrics."""
    if success:
        embeddings_generated_total.labels(model=model).inc()
        embedding_generation_duration_seconds.labels(model=model).observe(duration)
    else:
        embedding_generation_errors_total.labels(model=model, error_type=error_type or "unknown").inc()


def track_search(duration: float, result_count: int, success: bool = True):
    """Track search metrics."""
    status = "success" if success else "error"
    search_requests_total.labels(status=status).inc()
    search_duration_seconds.observe(duration)
    if success:
        search_results_count.observe(result_count)


def track_ingestion(mode: str, status: str, duration: float = None, doc_count: int = 0):
    """Track ingestion metrics."""
    ingestion_jobs_total.labels(mode=mode, status=status).inc()
    if doc_count > 0:
        ingestion_documents_total.labels(status=status).inc(doc_count)
    if duration is not None:
        ingestion_duration_seconds.labels(mode=mode).observe(duration)


def init_service_metrics(version: str, environment: str):
    """Initialize service metrics."""
    service_info.labels(version=version, environment=environment).set(1)
    service_up.set(1)


def get_metrics_response() -> Response:
    """Get Prometheus metrics as HTTP response."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# Context Managers
# ============================================================================

class track_time:
    """Context manager to track operation duration."""
    
    def __init__(self, metric_name: str = None):
        self.metric_name = metric_name
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        return False  # Don't suppress exceptions

