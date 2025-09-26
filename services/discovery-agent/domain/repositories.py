"""Repository interfaces and implementations for Service Discovery domain.

This module defines repository patterns for persisting and retrieving
service discovery domain objects.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import uuid4

try:
    from services.shared.domain.repositories.base_repository import BaseRepository, InMemoryRepository
except ImportError:
    # Fallback for test environments or different working directories
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    while current_dir.parent != current_dir:
        shared_path = current_dir.parent / "shared" / "domain" / "repositories" / "base_repository.py"
        if shared_path.exists():
            sys.path.insert(0, str(shared_path.parent.parent.parent.parent))
            break
        current_dir = current_dir.parent
    from services.shared.domain.repositories.base_repository import BaseRepository, InMemoryRepository
from .entities import Service, Endpoint


class ServiceRepository(BaseRepository[Service], ABC):
    """Abstract repository for Service entities."""

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Service]:
        """Find service by name."""
        pass

    @abstractmethod
    async def find_by_base_url(self, base_url: str) -> Optional[Service]:
        """Find service by base URL."""
        pass

    @abstractmethod
    async def find_active_services(self) -> List[Service]:
        """Find all active services."""
        pass

    @abstractmethod
    async def find_services_by_tag(self, tag: str) -> List[Service]:
        """Find services that have endpoints with a specific tag."""
        pass


class InMemoryServiceRepository(InMemoryRepository[Service], ServiceRepository):
    """In-memory implementation of ServiceRepository."""

    def __init__(self):
        super().__init__()
        self._name_index: dict[str, str] = {}  # name -> service_id
        self._url_index: dict[str, str] = {}   # base_url -> service_id

    async def save(self, entity: Service) -> Service:
        """Save service and update indexes."""
        saved = await super().save(entity)

        # Update indexes
        self._name_index[saved.name] = saved.id
        self._url_index[saved.base_url] = saved.id

        return saved

    async def delete(self, entity_id: str) -> bool:
        """Delete service and clean up indexes."""
        service = await self.find_by_id(entity_id)
        if service:
            # Clean up indexes
            if service.name in self._name_index:
                del self._name_index[service.name]
            if service.base_url in self._url_index:
                del self._url_index[service.base_url]

        return await super().delete(entity_id)

    async def find_by_name(self, name: str) -> Optional[Service]:
        """Find service by name."""
        service_id = self._name_index.get(name)
        if service_id:
            return await self.find_by_id(service_id)
        return None

    async def find_by_base_url(self, base_url: str) -> Optional[Service]:
        """Find service by base URL."""
        service_id = self._url_index.get(base_url)
        if service_id:
            return await self.find_by_id(service_id)
        return None

    async def find_active_services(self) -> List[Service]:
        """Find all active services."""
        all_services = await self.find_all()
        return [service for service in all_services if service.status == "active"]

    async def find_services_by_tag(self, tag: str) -> List[Service]:
        """Find services that have endpoints with a specific tag."""
        all_services = await self.find_all()
        matching_services = []

        for service in all_services:
            if any(tag in endpoint.tags for endpoint in service.endpoints):
                matching_services.append(service)

        return matching_services


class EndpointRepository(BaseRepository[Endpoint], ABC):
    """Abstract repository for Endpoint entities."""

    @abstractmethod
    async def find_by_service_id(self, service_id: str) -> List[Endpoint]:
        """Find all endpoints for a service."""
        pass

    @abstractmethod
    async def find_by_path_and_method(self, path: str, method: str) -> Optional[Endpoint]:
        """Find endpoint by path and method."""
        pass

    @abstractmethod
    async def find_by_tag(self, tag: str) -> List[Endpoint]:
        """Find endpoints with a specific tag."""
        pass


class InMemoryEndpointRepository(InMemoryRepository[Endpoint], EndpointRepository):
    """In-memory implementation of EndpointRepository."""

    def __init__(self):
        super().__init__()
        self._service_index: dict[str, List[str]] = {}  # service_id -> [endpoint_ids]
        self._path_method_index: dict[str, str] = {}    # "path:method" -> endpoint_id

    async def save(self, entity: Endpoint) -> Endpoint:
        """Save endpoint and update indexes."""
        saved = await super().save(entity)

        # Update service index
        if saved.service_id:
            if saved.service_id not in self._service_index:
                self._service_index[saved.service_id] = []
            if saved.id not in self._service_index[saved.service_id]:
                self._service_index[saved.service_id].append(saved.id)

        # Update path-method index
        key = f"{saved.path}:{saved.method}"
        self._path_method_index[key] = saved.id

        return saved

    async def delete(self, entity_id: str) -> bool:
        """Delete endpoint and clean up indexes."""
        endpoint = await self.find_by_id(entity_id)
        if endpoint:
            # Clean up service index
            if endpoint.service_id and endpoint.service_id in self._service_index:
                if entity_id in self._service_index[endpoint.service_id]:
                    self._service_index[endpoint.service_id].remove(entity_id)
                    if not self._service_index[endpoint.service_id]:
                        del self._service_index[endpoint.service_id]

            # Clean up path-method index
            key = f"{endpoint.path}:{endpoint.method}"
            if key in self._path_method_index:
                del self._path_method_index[key]

        return await super().delete(entity_id)

    async def find_by_service_id(self, service_id: str) -> List[Endpoint]:
        """Find all endpoints for a service."""
        endpoint_ids = self._service_index.get(service_id, [])
        endpoints = []
        for endpoint_id in endpoint_ids:
            endpoint = await self.find_by_id(endpoint_id)
            if endpoint:
                endpoints.append(endpoint)
        return endpoints

    async def find_by_path_and_method(self, path: str, method: str) -> Optional[Endpoint]:
        """Find endpoint by path and method."""
        key = f"{path}:{method}"
        endpoint_id = self._path_method_index.get(key)
        if endpoint_id:
            return await self.find_by_id(endpoint_id)
        return None

    async def find_by_tag(self, tag: str) -> List[Endpoint]:
        """Find endpoints with a specific tag."""
        all_endpoints = await self.find_all()
        return [endpoint for endpoint in all_endpoints if tag in endpoint.tags]
