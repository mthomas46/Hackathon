"""Log Collector REST API."""

from fastapi import APIRouter

# Import dependencies (these would normally come from dependency injection)
from ...domain.services.log_stats import LogStatsService
from ...domain.services.log_storage import LogStorageService

# Create dependencies (mock implementations for now)
_log_stats_service = LogStatsService()
_log_storage_service = LogStorageService()

# Import and create routers
from .routes.analytics import create_analytics_router

# Create API router
api_router = APIRouter()
api_router.include_router(create_analytics_router(_log_stats_service, _log_storage_service))

__all__ = ["api_router"]