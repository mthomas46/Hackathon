"""Log Collector REST API."""

from fastapi import APIRouter

# Import dependencies (these would normally come from dependency injection)
from ...application.use_cases.collect_logs_use_case import CollectLogsUseCase
from ...domain.services.log_storage import LogStorageService
from ...domain.services.log_stats import LogStatsService

# Create dependencies
_log_storage_service = LogStorageService()
_log_stats_service = LogStatsService()
_collect_logs_use_case = CollectLogsUseCase(_log_storage_service, _log_stats_service)

# Create API router
api_router = APIRouter()

# Health endpoint
@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "log-collector",
        "version": "1.0.0"
    }

__all__ = ["api_router"]
