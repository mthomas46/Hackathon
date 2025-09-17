"""Service Interfaces and Contracts - Dependency injection service definitions."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol, TypeVar, Generic, Union
from datetime import datetime

T = TypeVar('T')


# Domain Service Interfaces
class IAnalysisService(Protocol):
    """Analysis service interface."""

    async def analyze_documents(self, targets: List[str], analysis_type: str, **kwargs) -> Dict[str, Any]:
        """Analyze documents."""
        ...

    async def get_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis status."""
        ...


class IDocumentService(Protocol):
    """Document service interface."""

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        ...

    async def list_documents(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List documents with filters."""
        ...

    async def create_document(self, document_data: Dict[str, Any]) -> str:
        """Create new document."""
        ...


class IRepositoryService(Protocol):
    """Repository service interface."""

    async def get_repository_info(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        ...

    async def list_repositories(self) -> List[Dict[str, Any]]:
        """List all repositories."""
        ...

    async def connect_repository(self, config: Dict[str, Any]) -> str:
        """Connect to repository."""
        ...


# Infrastructure Service Interfaces
class ICacheService(Protocol):
    """Cache service interface."""

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ...

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        ...


class IEventPublisher(Protocol):
    """Event publisher interface."""

    async def publish(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish event."""
        ...

    async def publish_batch(self, events: List[Dict[str, Any]]) -> None:
        """Publish batch of events."""
        ...


class ILoggerService(Protocol):
    """Logger service interface."""

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        ...

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        ...

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        ...

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        ...

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        ...


class IMetricsService(Protocol):
    """Metrics service interface."""

    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment counter metric."""
        ...

    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record histogram metric."""
        ...

    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record gauge metric."""
        ...


class IConfigurationService(Protocol):
    """Configuration service interface."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        ...

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get configuration section."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        ...


class IServiceClient(Protocol):
    """Service client interface."""

    async def get_json(self, url: str, **kwargs) -> Optional[Any]:
        """Make GET request and return JSON."""
        ...

    async def post_json(self, url: str, data: Any, **kwargs) -> Optional[Any]:
        """Make POST request with JSON data."""
        ...

    def doc_store_url(self) -> str:
        """Get document store URL."""
        ...

    def analysis_service_url(self) -> str:
        """Get analysis service URL."""
        ...


# External Service Interfaces
class ISemanticAnalyzer(Protocol):
    """Semantic analyzer interface."""

    async def analyze_similarity(self, texts: List[str], **kwargs) -> Dict[str, Any]:
        """Analyze semantic similarity."""
        ...

    async def find_similar(self, target: str, candidates: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Find similar texts."""
        ...


class ISentimentAnalyzer(Protocol):
    """Sentiment analyzer interface."""

    async def analyze_sentiment(self, text: str, **kwargs) -> Dict[str, Any]:
        """Analyze sentiment of text."""
        ...

    async def analyze_batch(self, texts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Analyze sentiment of multiple texts."""
        ...


class IQualityAnalyzer(Protocol):
    """Quality analyzer interface."""

    async def assess_quality(self, content: str, **kwargs) -> Dict[str, Any]:
        """Assess content quality."""
        ...

    async def analyze_readability(self, content: str) -> Dict[str, Any]:
        """Analyze content readability."""
        ...


# Repository Interfaces
class IAnalysisRepository(Protocol[T]):
    """Analysis repository interface."""

    async def save(self, analysis: T) -> None:
        """Save analysis."""
        ...

    async def get_by_id(self, analysis_id: str) -> Optional[T]:
        """Get analysis by ID."""
        ...

    async def get_by_status(self, status: str) -> List[T]:
        """Get analyses by status."""
        ...

    async def delete(self, analysis_id: str) -> None:
        """Delete analysis."""
        ...


class IDocumentRepository(Protocol[T]):
    """Document repository interface."""

    async def save(self, document: T) -> None:
        """Save document."""
        ...

    async def get_by_id(self, doc_id: str) -> Optional[T]:
        """Get document by ID."""
        ...

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """Find documents by criteria."""
        ...

    async def delete(self, doc_id: str) -> None:
        """Delete document."""
        ...


class IFindingRepository(Protocol[T]):
    """Finding repository interface."""

    async def save(self, finding: T) -> None:
        """Save finding."""
        ...

    async def get_by_analysis_id(self, analysis_id: str) -> List[T]:
        """Get findings by analysis ID."""
        ...

    async def get_by_severity(self, severity: str) -> List[T]:
        """Get findings by severity."""
        ...

    async def delete_by_analysis_id(self, analysis_id: str) -> None:
        """Delete findings by analysis ID."""
        ...


# Factory Interfaces
class IServiceFactory(Protocol[T]):
    """Service factory interface."""

    def create(self, **kwargs) -> T:
        """Create service instance."""
        ...

    def create_with_dependencies(self, container: Any, **kwargs) -> T:
        """Create service instance with dependency injection."""
        ...


class IHandlerFactory(Protocol[T]):
    """Handler factory interface."""

    def create_handler(self, handler_type: str, **kwargs) -> T:
        """Create handler instance."""
        ...

    def get_available_handlers(self) -> List[str]:
        """Get list of available handlers."""
        ...


# Validation Interfaces
class IValidator(Protocol):
    """Validator interface."""

    async def validate(self, data: Any) -> Dict[str, Any]:
        """Validate data."""
        ...

    def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules."""
        ...


class IBusinessRuleValidator(Protocol):
    """Business rule validator interface."""

    async def validate_business_rule(self, entity: Any, rule_name: str) -> Dict[str, Any]:
        """Validate business rule."""
        ...

    def get_supported_rules(self) -> List[str]:
        """Get supported business rules."""
        ...


# Abstract Base Classes
class BaseService(ABC):
    """Base service class with common functionality."""

    def __init__(self, logger: ILoggerService, metrics: Optional[IMetricsService] = None) -> None:
        self._logger = logger
        self._metrics = metrics

    async def _log_operation(self, operation: str, **kwargs) -> None:
        """Log operation with structured data."""
        if self._logger:
            await self._logger.info(f"Service operation: {operation}", **kwargs)

    async def _record_metric(self, name: str, value: float, **tags) -> None:
        """Record metric if metrics service is available."""
        if self._metrics:
            await self._metrics.record_histogram(name, value, tags)


class BaseRepository(ABC):
    """Base repository class with common functionality."""

    def __init__(self, cache: Optional[ICacheService] = None, logger: Optional[ILoggerService] = None) -> None:
        self._cache = cache
        self._logger = logger

    async def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache if available."""
        if self._cache:
            return await self._cache.get(key)
        return None

    async def _set_cached(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache if available."""
        if self._cache:
            await self._cache.set(key, value, ttl)
