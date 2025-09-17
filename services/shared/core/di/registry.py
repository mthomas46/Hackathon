"""Service Registry - Central service registration and configuration."""

import os
from typing import Dict, Any, Type, Optional, List
from .container import DependencyContainer, ServiceLifetime, get_global_container
from .services import (
    IAnalysisService, IDocumentService, IRepositoryService,
    ICacheService, IEventPublisher, ILoggerService, IMetricsService,
    IConfigurationService, IServiceClient,
    ISemanticAnalyzer, ISentimentAnalyzer, IQualityAnalyzer,
    IAnalysisRepository, IDocumentRepository, IFindingRepository,
    BaseService, BaseRepository
)


class ServiceRegistry:
    """Central service registry for dependency injection configuration."""

    def __init__(self, container: Optional[DependencyContainer] = None) -> None:
        self._container = container or get_global_container()
        self._services_registered = False

    def register_all_services(self) -> DependencyContainer:
        """Register all services with the container."""
        if self._services_registered:
            return self._container

        # Register core infrastructure services
        self._register_infrastructure_services()

        # Register domain services
        self._register_domain_services()

        # Register repository services
        self._register_repository_services()

        # Register external services
        self._register_external_services()

        # Register cross-cutting concerns
        self._register_cross_cutting_services()

        self._services_registered = True
        return self._container

    def _register_infrastructure_services(self) -> None:
        """Register infrastructure services."""

        # Configuration Service
        from ..config.config import ConfigService
        self._container.register_singleton(
            IConfigurationService,
            ConfigService
        )

        # Logger Service
        from ..logging import LoggerService
        self._container.register_singleton(
            ILoggerService,
            LoggerService
        )

        # Metrics Service
        from ..monitoring.metrics import MetricsService
        self._container.register_singleton(
            IMetricsService,
            MetricsService
        )

        # Cache Service
        from ..caching.cache import CacheService
        self._container.register_singleton(
            ICacheService,
            CacheService
        )

        # Event Publisher
        from ..streaming.event_publisher import EventPublisher
        self._container.register_singleton(
            IEventPublisher,
            EventPublisher
        )

        # Service Client
        from ..utilities.service_client import ServiceClient
        self._container.register_singleton(
            IServiceClient,
            ServiceClient
        )

    def _register_domain_services(self) -> None:
        """Register domain services."""

        # Analysis Service
        from ...domain.services.analysis_service import AnalysisService
        self._container.register_singleton(
            IAnalysisService,
            AnalysisService
        )

        # Document Service
        from ...domain.services.document_service import DocumentService
        self._container.register_singleton(
            IDocumentService,
            DocumentService
        )

        # Repository Service
        from ...domain.services.repository_service import RepositoryService
        self._container.register_singleton(
            IRepositoryService,
            RepositoryService
        )

    def _register_repository_services(self) -> None:
        """Register repository services."""

        # Analysis Repository
        from ...infrastructure.repositories.analysis_repository import AnalysisRepository
        self._container.register_scoped(
            IAnalysisRepository,
            AnalysisRepository
        )

        # Document Repository
        from ...infrastructure.repositories.document_repository import DocumentRepository
        self._container.register_scoped(
            IDocumentRepository,
            DocumentRepository
        )

        # Finding Repository
        from ...infrastructure.repositories.finding_repository import FindingRepository
        self._container.register_scoped(
            IFindingRepository,
            FindingRepository
        )

    def _register_external_services(self) -> None:
        """Register external service adapters."""

        # Semantic Analyzer
        from ...infrastructure.external.semantic_analyzer_adapter import SemanticAnalyzerAdapter
        self._container.register_singleton(
            ISemanticAnalyzer,
            SemanticAnalyzerAdapter
        )

        # Sentiment Analyzer
        from ...infrastructure.external.sentiment_analyzer_adapter import SentimentAnalyzerAdapter
        self._container.register_singleton(
            ISentimentAnalyzer,
            SentimentAnalyzerAdapter
        )

        # Quality Analyzer
        from ...infrastructure.external.quality_analyzer_adapter import QualityAnalyzerAdapter
        self._container.register_singleton(
            IQualityAnalyzer,
            QualityAnalyzerAdapter
        )

    def _register_cross_cutting_services(self) -> None:
        """Register cross-cutting concern services."""

        # Register factories
        from ...application.factories.handler_factory import HandlerFactory
        self._container.register_singleton(
            Type[HandlerFactory],
            HandlerFactory
        )

        # Register validators
        from ...application.validators.business_rule_validator import BusinessRuleValidator
        self._container.register_singleton(
            Type[BusinessRuleValidator],
            BusinessRuleValidator
        )

    def register_custom_service(self, interface: Type, implementation: Type, lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> None:
        """Register a custom service."""
        if lifetime == ServiceLifetime.SINGLETON:
            self._container.register_singleton(interface, implementation)
        elif lifetime == ServiceLifetime.SCOPED:
            self._container.register_scoped(interface, implementation)
        else:
            self._container.register_transient(interface, implementation)

    def register_service_instance(self, interface: Type, instance: Any) -> None:
        """Register a service instance."""
        self._container.register_instance(interface, instance)

    def register_factory(self, interface: Type, factory_func, lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """Register a service factory."""
        self._container.register_factory(interface, factory_func, lifetime)

    def get_service(self, interface: Type) -> Any:
        """Get service instance."""
        return self._container.resolve(interface)

    def create_scope(self):
        """Create a new service scope."""
        return self._container.create_scope()


# Global registry instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry."""
    global _service_registry
    if _service_registry is None:
        container = get_global_container()
        _service_registry = ServiceRegistry(container)
        _service_registry.register_all_services()
    return _service_registry


def initialize_services() -> None:
    """Initialize all services - call this at application startup."""
    registry = get_service_registry()

    # Initialize any services that need startup
    try:
        config_service = registry.get_service(IConfigurationService)
        logger_service = registry.get_service(ILoggerService)
        metrics_service = registry.get_service(IMetricsService)

        # Log initialization
        logger_service.info("Services initialized successfully", {
            "service_count": len(registry._container._services),
            "environment": os.getenv("ENVIRONMENT", "development")
        })

    except Exception as e:
        print(f"Failed to initialize services: {e}")
        raise


def get_service(interface: Type) -> Any:
    """Get service instance from global registry."""
    return get_service_registry().get_service(interface)


def create_service_scope():
    """Create a new service scope from global registry."""
    return get_service_registry().create_scope()


# Convenience functions for common services
def get_analysis_service() -> IAnalysisService:
    """Get analysis service."""
    return get_service(IAnalysisService)


def get_document_service() -> IDocumentService:
    """Get document service."""
    return get_service(IDocumentService)


def get_cache_service() -> ICacheService:
    """Get cache service."""
    return get_service(ICacheService)


def get_logger_service() -> ILoggerService:
    """Get logger service."""
    return get_service(ILoggerService)


def get_metrics_service() -> IMetricsService:
    """Get metrics service."""
    return get_service(IMetricsService)


def get_config_service() -> IConfigurationService:
    """Get configuration service."""
    return get_service(IConfigurationService)
