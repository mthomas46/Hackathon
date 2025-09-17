"""Base Analysis Handler - Common functionality for all analysis handlers."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None

try:
    from services.shared.models import Document, Finding
except ImportError:
    # Fallback for testing or when shared services are not available
    class Document:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class Finding:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

try:
    from services.shared.utilities import get_service_client
except ImportError:
    # Fallback for testing or when shared services are not available
    def get_service_client(service_name):
        return None


logger = logging.getLogger(__name__)


class AnalysisResult:
    """Standardized analysis result structure."""

    def __init__(self,
                 analysis_id: str,
                 status: str = "completed",
                 data: Optional[Dict[str, Any]] = None,
                 error_message: Optional[str] = None,
                 execution_time_seconds: Optional[float] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.analysis_id = analysis_id
        self.status = status
        self.data = data or {}
        self.error_message = error_message
        self.execution_time_seconds = execution_time_seconds
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc)


class BaseAnalysisHandler(ABC):
    """Base class for all analysis handlers providing common functionality."""

    def __init__(self, handler_name: str):
        self.handler_name = handler_name
        self.logger = logging.getLogger(f"{__name__}.{handler_name}")

    async def _get_service_client(self):
        """Get service client for external service communication."""
        return get_service_client("analysis-service")

    async def _fetch_documents(self, document_ids: List[str]) -> List[Document]:
        """Fetch documents from document store."""
        documents = []
        service_client = await self._get_service_client()

        if not service_client:
            self.logger.warning("Service client not available")
            return documents

        for doc_id in document_ids:
            try:
                doc_data = await service_client.get_json(
                    f"{service_client.doc_store_url()}/documents/{doc_id}"
                )
                if doc_data:
                    documents.append(Document(**doc_data))
            except Exception as e:
                self.logger.error(f"Failed to fetch document {doc_id}: {e}")

        return documents

    async def _publish_event(self, event_type: str, event_data: Dict[str, Any]):
        """Publish event to Redis for external systems."""
        if not aioredis:
            return

        try:
            from services.shared.config import get_config_value
            redis_host = get_config_value("REDIS_HOST", "redis", section="redis", env_key="REDIS_HOST")
            client = aioredis.from_url(f"redis://{redis_host}")

            event_payload = {
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "handler": self.handler_name,
                **event_data
            }

            await client.publish(event_type, event_payload)
            await client.close()

        except Exception as e:
            self.logger.error(f"Failed to publish event {event_type}: {e}")

    def _create_analysis_result(self,
                              analysis_id: str,
                              data: Optional[Dict[str, Any]] = None,
                              error_message: Optional[str] = None,
                              execution_time: Optional[float] = None) -> AnalysisResult:
        """Create standardized analysis result."""
        return AnalysisResult(
            analysis_id=analysis_id,
            data=data,
            error_message=error_message,
            execution_time_seconds=execution_time
        )

    async def _handle_error(self,
                          error: Exception,
                          analysis_id: str,
                          context: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """Handle errors consistently across handlers."""
        error_message = f"{type(error).__name__}: {str(error)}"
        self.logger.error(f"Analysis {analysis_id} failed: {error_message}", extra=context)

        # Publish error event
        await self._publish_event("analysis.error", {
            "analysis_id": analysis_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "handler": self.handler_name,
            "context": context or {}
        })

        return self._create_analysis_result(
            analysis_id=analysis_id,
            error_message=error_message
        )

    async def _log_analysis_start(self, analysis_id: str, analysis_type: str, metadata: Optional[Dict[str, Any]] = None):
        """Log analysis start event."""
        self.logger.info(f"Starting {analysis_type} analysis", extra={
            "analysis_id": analysis_id,
            "analysis_type": analysis_type,
            "handler": self.handler_name,
            "metadata": metadata or {}
        })

        await self._publish_event("analysis.started", {
            "analysis_id": analysis_id,
            "analysis_type": analysis_type,
            "handler": self.handler_name,
            "metadata": metadata or {}
        })

    async def _log_analysis_complete(self,
                                   analysis_id: str,
                                   analysis_type: str,
                                   execution_time: float,
                                   result_summary: Optional[Dict[str, Any]] = None):
        """Log analysis completion event."""
        self.logger.info(f"Completed {analysis_type} analysis in {execution_time:.2f}s", extra={
            "analysis_id": analysis_id,
            "analysis_type": analysis_type,
            "handler": self.handler_name,
            "execution_time": execution_time,
            "result_summary": result_summary or {}
        })

        await self._publish_event("analysis.completed", {
            "analysis_id": analysis_id,
            "analysis_type": analysis_type,
            "handler": self.handler_name,
            "execution_time": execution_time,
            "result_summary": result_summary or {}
        })

    @abstractmethod
    async def handle(self, request) -> AnalysisResult:
        """Handle the analysis request. Must be implemented by subclasses."""
        pass

    async def execute_with_timing(self, request) -> AnalysisResult:
        """Execute analysis with timing and error handling."""
        analysis_id = getattr(request, 'analysis_id', f"{self.handler_name}-{int(time.time())}")
        analysis_type = self.handler_name.replace('_', '-')

        start_time = time.time()

        try:
            await self._log_analysis_start(analysis_id, analysis_type)

            result = await self.handle(request)
            result.execution_time_seconds = time.time() - start_time

            await self._log_analysis_complete(
                analysis_id,
                analysis_type,
                result.execution_time_seconds,
                {"status": result.status, "has_error": bool(result.error_message)}
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            return await self._handle_error(e, analysis_id, {
                "execution_time": execution_time,
                "analysis_type": analysis_type
            })


class HandlerRegistry:
    """Registry for managing analysis handlers."""

    def __init__(self):
        self._handlers: Dict[str, BaseAnalysisHandler] = {}

    def register(self, analysis_type: str, handler: BaseAnalysisHandler):
        """Register a handler for an analysis type."""
        self._handlers[analysis_type] = handler
        logger.info(f"Registered handler for analysis type: {analysis_type}")

    def get_handler(self, analysis_type: str) -> Optional[BaseAnalysisHandler]:
        """Get handler for analysis type."""
        return self._handlers.get(analysis_type)

    def list_handlers(self) -> List[str]:
        """List all registered handler types."""
        return list(self._handlers.keys())

    async def execute_analysis(self, analysis_type: str, request) -> Optional[AnalysisResult]:
        """Execute analysis using appropriate handler."""
        handler = self.get_handler(analysis_type)
        if not handler:
            logger.error(f"No handler registered for analysis type: {analysis_type}")
            return None

        return await handler.execute_with_timing(request)


# Global handler registry
handler_registry = HandlerRegistry()
