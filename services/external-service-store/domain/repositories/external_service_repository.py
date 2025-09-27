"""Repository interfaces for External Service Store.

This module defines the repository interfaces for managing external services
and their relationships in the domain layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.external_service import (
    ExternalService, ServiceEndpoint, ServiceDependency,
    ServiceDocument, ServiceUser, ServiceTopic,
    ServiceStatus, ServiceType
)


class ExternalServiceRepository(ABC):
    """Abstract repository for ExternalService entities."""

    @abstractmethod
    async def save(self, service: ExternalService) -> None:
        """Save an external service."""
        pass

    @abstractmethod
    async def find_by_id(self, service_id: str) -> Optional[ExternalService]:
        """Find service by ID."""
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[ExternalService]:
        """Find service by name."""
        pass

    @abstractmethod
    async def find_by_status(self, status: ServiceStatus) -> List[ExternalService]:
        """Find services by status."""
        pass

    @abstractmethod
    async def find_by_type(self, service_type: ServiceType) -> List[ExternalService]:
        """Find services by type."""
        pass

    @abstractmethod
    async def find_services_by_technology(self, technology: str) -> List[ExternalService]:
        """Find services using a specific technology."""
        pass

    @abstractmethod
    async def find_services_by_topic(self, topic: str) -> List[ExternalService]:
        """Find services related to a topic."""
        pass

    @abstractmethod
    async def find_services_by_user(self, user_id: str) -> List[ExternalService]:
        """Find services related to a user."""
        pass

    @abstractmethod
    async def search_services(self, query: str, limit: int = 50) -> List[ExternalService]:
        """Search services by name, description, or tags."""
        pass

    @abstractmethod
    async def list_all_services(self, limit: int = 100, offset: int = 0) -> List[ExternalService]:
        """List all services with pagination."""
        pass

    @abstractmethod
    async def update(self, service: ExternalService) -> None:
        """Update an existing service."""
        pass

    @abstractmethod
    async def delete(self, service_id: str) -> bool:
        """Delete a service."""
        pass

    @abstractmethod
    async def exists(self, service_id: str) -> bool:
        """Check if service exists."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total services."""
        pass


class ServiceEndpointRepository(ABC):
    """Abstract repository for ServiceEndpoint entities."""

    @abstractmethod
    async def save(self, endpoint: ServiceEndpoint) -> None:
        """Save an endpoint."""
        pass

    @abstractmethod
    async def find_by_id(self, endpoint_id: str) -> Optional[ServiceEndpoint]:
        """Find endpoint by ID."""
        pass

    @abstractmethod
    async def find_by_service(self, service_id: str) -> List[ServiceEndpoint]:
        """Find all endpoints for a service."""
        pass

    @abstractmethod
    async def find_by_path_and_method(self, service_id: str, path: str, method: str) -> Optional[ServiceEndpoint]:
        """Find endpoint by service, path, and method."""
        pass

    @abstractmethod
    async def update(self, endpoint: ServiceEndpoint) -> None:
        """Update an endpoint."""
        pass

    @abstractmethod
    async def delete(self, endpoint_id: str) -> bool:
        """Delete an endpoint."""
        pass

    @abstractmethod
    async def delete_by_service(self, service_id: str) -> int:
        """Delete all endpoints for a service. Returns count deleted."""
        pass


class ServiceDependencyRepository(ABC):
    """Abstract repository for ServiceDependency entities."""

    @abstractmethod
    async def save(self, dependency: ServiceDependency) -> None:
        """Save a dependency."""
        pass

    @abstractmethod
    async def find_by_id(self, dependency_id: str) -> Optional[ServiceDependency]:
        """Find dependency by ID."""
        pass

    @abstractmethod
    async def find_dependencies_by_service(self, service_id: str) -> List[ServiceDependency]:
        """Find all dependencies for a service."""
        pass

    @abstractmethod
    async def find_dependents_of_service(self, service_id: str) -> List[ServiceDependency]:
        """Find all services that depend on the given service."""
        pass

    @abstractmethod
    async def find_by_type(self, dependency_type: str) -> List[ServiceDependency]:
        """Find dependencies by type."""
        pass

    @abstractmethod
    async def update(self, dependency: ServiceDependency) -> None:
        """Update a dependency."""
        pass

    @abstractmethod
    async def delete(self, dependency_id: str) -> bool:
        """Delete a dependency."""
        pass

    @abstractmethod
    async def delete_by_service(self, service_id: str) -> int:
        """Delete all dependencies for a service. Returns count deleted."""
        pass


class ServiceDocumentRepository(ABC):
    """Abstract repository for ServiceDocument entities."""

    @abstractmethod
    async def save(self, document: ServiceDocument) -> None:
        """Save a document relationship."""
        pass

    @abstractmethod
    async def find_by_id(self, document_id: str) -> Optional[ServiceDocument]:
        """Find document relationship by ID."""
        pass

    @abstractmethod
    async def find_by_service(self, service_id: str) -> List[ServiceDocument]:
        """Find all documents for a service."""
        pass

    @abstractmethod
    async def find_by_document(self, document_id: str) -> List[ServiceDocument]:
        """Find all services related to a document."""
        pass

    @abstractmethod
    async def find_by_type(self, document_type: str) -> List[ServiceDocument]:
        """Find documents by type."""
        pass

    @abstractmethod
    async def find_recent_by_service_and_type(self, service_id: str, doc_type: str, limit: int = 1) -> List[ServiceDocument]:
        """Find recent documents of specific type for a service."""
        pass

    @abstractmethod
    async def update(self, document: ServiceDocument) -> None:
        """Update a document relationship."""
        pass

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete a document relationship."""
        pass

    @abstractmethod
    async def delete_by_service(self, service_id: str) -> int:
        """Delete all document relationships for a service. Returns count deleted."""
        pass

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> int:
        """Delete all service relationships for a document. Returns count deleted."""
        pass

    async def list_all_documents(self, limit: int = 1000) -> List[ServiceDocument]:
        """List all document relationships with optional limit."""
        pass


class ServiceUserRepository(ABC):
    """Abstract repository for ServiceUser entities."""

    @abstractmethod
    async def save(self, user: ServiceUser) -> None:
        """Save a user relationship."""
        pass

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[ServiceUser]:
        """Find user relationship by ID."""
        pass

    @abstractmethod
    async def find_by_service(self, service_id: str) -> List[ServiceUser]:
        """Find all users for a service."""
        pass

    @abstractmethod
    async def find_by_user(self, user_id: str) -> List[ServiceUser]:
        """Find all services for a user."""
        pass

    @abstractmethod
    async def find_by_relationship_type(self, relationship_type: str) -> List[ServiceUser]:
        """Find user relationships by type."""
        pass

    @abstractmethod
    async def find_maintainers_by_service(self, service_id: str) -> List[ServiceUser]:
        """Find maintainers for a service."""
        pass

    @abstractmethod
    async def update(self, user: ServiceUser) -> None:
        """Update a user relationship."""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user relationship."""
        pass

    @abstractmethod
    async def delete_by_service(self, service_id: str) -> int:
        """Delete all user relationships for a service. Returns count deleted."""
        pass

    @abstractmethod
    async def delete_by_user(self, user_id: str) -> int:
        """Delete all service relationships for a user. Returns count deleted."""
        pass


class ServiceTopicRepository(ABC):
    """Abstract repository for ServiceTopic entities."""

    @abstractmethod
    async def save(self, topic: ServiceTopic) -> None:
        """Save a topic relationship."""
        pass

    @abstractmethod
    async def find_by_id(self, topic_id: str) -> Optional[ServiceTopic]:
        """Find topic relationship by ID."""
        pass

    @abstractmethod
    async def find_by_service(self, service_id: str) -> List[ServiceTopic]:
        """Find all topics for a service."""
        pass

    @abstractmethod
    async def find_by_topic(self, topic: str) -> List[ServiceTopic]:
        """Find all services related to a topic."""
        pass

    @abstractmethod
    async def find_by_relevance_score(self, min_score: int = 50) -> List[ServiceTopic]:
        """Find topic relationships above minimum relevance score."""
        pass

    @abstractmethod
    async def update(self, topic: ServiceTopic) -> None:
        """Update a topic relationship."""
        pass

    @abstractmethod
    async def delete(self, topic_id: str) -> bool:
        """Delete a topic relationship."""
        pass

    @abstractmethod
    async def delete_by_service(self, service_id: str) -> int:
        """Delete all topic relationships for a service. Returns count deleted."""
        pass

    @abstractmethod
    async def delete_by_topic(self, topic: str) -> int:
        """Delete all service relationships for a topic. Returns count deleted."""
        pass
