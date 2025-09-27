"""External Service Domain Service.

This module provides the domain service for managing external services,
their relationships, and metadata.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from ..entities.external_service import (
    ExternalService, ServiceEndpoint, ServiceDependency,
    ServiceDocument, ServiceUser, ServiceTopic,
    ServiceStatus, ServiceType
)
from ..repositories.external_service_repository import (
    ExternalServiceRepository, ServiceEndpointRepository,
    ServiceDependencyRepository, ServiceDocumentRepository,
    ServiceUserRepository, ServiceTopicRepository
)


class ExternalServiceService:
    """Domain service for external service management."""

    def __init__(
        self,
        service_repo: ExternalServiceRepository,
        endpoint_repo: ServiceEndpointRepository,
        dependency_repo: ServiceDependencyRepository,
        document_repo: ServiceDocumentRepository,
        user_repo: ServiceUserRepository,
        topic_repo: ServiceTopicRepository
    ):
        """Initialize the service with all required repositories."""
        self._service_repo = service_repo
        self._endpoint_repo = endpoint_repo
        self._dependency_repo = dependency_repo
        self._document_repo = document_repo
        self._user_repo = user_repo
        self._topic_repo = topic_repo

    async def create_service(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: str = "",
        service_type: str = "api",
        version: str = "1.0.0"
    ) -> ExternalService:
        """Create a new external service."""
        # Check if service name already exists
        existing = await self._service_repo.find_by_name(name)
        if existing:
            raise ValueError(f"Service with name '{name}' already exists")

        service = ExternalService(
            name=name,
            display_name=display_name or name.replace('-', ' ').replace('_', ' ').title(),
            description=description,
            service_type=getattr(ServiceType, service_type.upper(), ServiceType.OTHER),
            version=version
        )

        await self._service_repo.save(service)
        return service

    async def get_service(self, service_id: str) -> Optional[ExternalService]:
        """Get a service by ID with all relationships loaded."""
        service = await self._service_repo.find_by_id(service_id)
        if not service:
            return None

        # Load all relationships
        service.endpoints = await self._endpoint_repo.find_by_service(service_id)
        service.dependencies = await self._dependency_repo.find_dependencies_by_service(service_id)
        service.documents = await self._document_repo.find_by_service(service_id)
        service.users = await self._user_repo.find_by_service(service_id)
        service.topics = await self._topic_repo.find_by_service(service_id)

        return service

    async def update_service(
        self,
        service_id: str,
        **updates
    ) -> ExternalService:
        """Update a service with the provided changes."""
        service = await self._service_repo.find_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")

        # Handle special fields
        if 'service_type' in updates:
            updates['service_type'] = getattr(ServiceType, updates['service_type'].upper(), ServiceType.OTHER)
        if 'status' in updates:
            updates['status'] = getattr(ServiceStatus, updates['status'].upper(), ServiceStatus.ACTIVE)
        if 'version' in updates:
            service.update_version(updates['version'])
            del updates['version']

        # Apply other updates
        for key, value in updates.items():
            if hasattr(service, key):
                setattr(service, key, value)

        service.updated_at = datetime.now(timezone.utc)
        await self._service_repo.update(service)
        return service

    async def delete_service(self, service_id: str) -> bool:
        """Delete a service and all its relationships."""
        service = await self._service_repo.find_by_id(service_id)
        if not service:
            return False

        # Delete all relationships
        await self._endpoint_repo.delete_by_service(service_id)
        await self._dependency_repo.delete_by_service(service_id)
        await self._document_repo.delete_by_service(service_id)
        await self._user_repo.delete_by_service(service_id)
        await self._topic_repo.delete_by_service(service_id)

        # Delete the service itself
        await self._service_repo.delete(service_id)
        return True

    async def list_services(
        self,
        status: Optional[str] = None,
        service_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ExternalService]:
        """List services with optional filtering."""
        if status:
            status_enum = getattr(ServiceStatus, status.upper(), None)
            if status_enum:
                return await self._service_repo.find_by_status(status_enum)

        if service_type:
            type_enum = getattr(ServiceType, service_type.upper(), None)
            if type_enum:
                return await self._service_repo.find_by_type(type_enum)

        return await self._service_repo.list_all_services(limit=limit, offset=offset)

    async def search_services(self, query: str, limit: int = 50) -> List[ExternalService]:
        """Search services by name, description, or tags."""
        return await self._service_repo.search_services(query, limit)

    # Endpoint management
    async def add_service_endpoint(
        self,
        service_id: str,
        path: str,
        method: str = "GET",
        description: str = "",
        request_contract: Optional[Dict[str, Any]] = None,
        response_contract: Optional[Dict[str, Any]] = None,
        response_types: Optional[List[str]] = None
    ) -> ServiceEndpoint:
        """Add an endpoint to a service."""
        service = await self._service_repo.find_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")

        # Check for duplicate endpoint
        existing = await self._endpoint_repo.find_by_path_and_method(service_id, path, method)
        if existing:
            raise ValueError(f"Endpoint {method} {path} already exists for service {service_id}")

        endpoint = ServiceEndpoint(
            path=path,
            method=method,
            description=description,
            request_contract=request_contract or {},
            response_contract=response_contract or {},
            response_types=response_types or []
        )

        service.add_endpoint(endpoint)
        await self._endpoint_repo.save(endpoint)
        await self._service_repo.update(service)

        return endpoint

    async def update_service_endpoint(
        self,
        service_id: str,
        endpoint_id: str,
        **updates
    ) -> ServiceEndpoint:
        """Update a service endpoint."""
        endpoint = await self._endpoint_repo.find_by_id(endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} not found")

        # Apply updates
        for key, value in updates.items():
            if hasattr(endpoint, key):
                setattr(endpoint, key, value)

        endpoint.updated_at = datetime.now(timezone.utc)
        await self._endpoint_repo.update(endpoint)

        return endpoint

    async def remove_service_endpoint(self, service_id: str, endpoint_id: str) -> bool:
        """Remove an endpoint from a service."""
        service = await self._service_repo.find_by_id(service_id)
        if not service:
            return False

        # Remove from service and repository
        if service.remove_endpoint(endpoint_id):
            await self._endpoint_repo.delete(endpoint_id)
            await self._service_repo.update(service)
            return True

        return False

    # Dependency management
    async def add_service_dependency(
        self,
        dependent_service_id: str,
        dependency_service_id: str,
        dependency_type: str = "runtime",
        version_constraint: Optional[str] = None,
        description: str = "",
        is_required: bool = True
    ) -> ServiceDependency:
        """Add a dependency between services."""
        # Validate services exist
        dependent = await self._service_repo.find_by_id(dependent_service_id)
        dependency = await self._service_repo.find_by_id(dependency_service_id)
        if not dependent or not dependency:
            raise ValueError("One or both services not found")

        dependency_rel = ServiceDependency(
            dependent_service_id=dependent_service_id,
            dependency_service_id=dependency_service_id,
            dependency_type=dependency_type,
            version_constraint=version_constraint,
            description=description,
            is_required=is_required
        )

        await self._dependency_repo.save(dependency_rel)
        return dependency_rel

    async def get_service_dependencies(self, service_id: str) -> List[ServiceDependency]:
        """Get all dependencies for a service."""
        return await self._dependency_repo.find_dependencies_by_service(service_id)

    async def get_service_dependents(self, service_id: str) -> List[ServiceDependency]:
        """Get all services that depend on the given service."""
        return await self._dependency_repo.find_dependents_of_service(service_id)

    # Document relationship management
    async def add_service_document(
        self,
        service_id: str,
        document_id: str,
        document_type: str,
        relationship_type: str = "reference",
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> ServiceDocument:
        """Add a document relationship to a service."""
        service = await self._service_repo.find_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")

        doc_rel = ServiceDocument(
            service_id=service_id,
            document_id=document_id,
            document_type=document_type,
            relationship_type=relationship_type,
            description=description,
            tags=tags or []
        )

        service.add_document_relationship(doc_rel)
        await self._document_repo.save(doc_rel)
        await self._service_repo.update(service)

        return doc_rel

    async def get_service_documents(self, service_id: str, doc_type: Optional[str] = None) -> List[ServiceDocument]:
        """Get all documents related to a service."""
        if doc_type:
            return await self._document_repo.find_recent_by_service_and_type(service_id, doc_type)
        return await self._document_repo.find_by_service(service_id)

    # User relationship management
    async def add_service_user(
        self,
        service_id: str,
        user_id: str,
        relationship_type: str = "maintainer",
        role: Optional[str] = None,
        permissions: Optional[List[str]] = None
    ) -> ServiceUser:
        """Add a user relationship to a service."""
        service = await self._service_repo.find_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")

        user_rel = ServiceUser(
            service_id=service_id,
            user_id=user_id,
            relationship_type=relationship_type,
            role=role,
            permissions=permissions or []
        )

        service.add_user_relationship(user_rel)
        await self._user_repo.save(user_rel)
        await self._service_repo.update(service)

        return user_rel

    async def get_service_users(self, service_id: str, relationship_type: Optional[str] = None) -> List[ServiceUser]:
        """Get all users related to a service."""
        if relationship_type:
            return await self._user_repo.find_maintainers_by_service(service_id) if relationship_type == "maintainer" else [
                user for user in await self._user_repo.find_by_service(service_id)
                if user.relationship_type == relationship_type
            ]
        return await self._user_repo.find_by_service(service_id)

    # Topic relationship management
    async def add_service_topic(
        self,
        service_id: str,
        topic: str,
        relevance_score: int = 50,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> ServiceTopic:
        """Add a topic relationship to a service."""
        service = await self._service_repo.find_by_id(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")

        topic_rel = ServiceTopic(
            service_id=service_id,
            topic=topic,
            relevance_score=relevance_score,
            description=description,
            tags=tags or []
        )

        service.add_topic_relationship(topic_rel)
        await self._topic_repo.save(topic_rel)
        await self._service_repo.update(service)

        return topic_rel

    async def get_service_topics(self, service_id: str) -> List[ServiceTopic]:
        """Get all topics related to a service."""
        return await self._topic_repo.find_by_service(service_id)

    # Analytics and insights
    async def get_service_health_overview(self) -> Dict[str, Any]:
        """Get an overview of service health and relationships."""
        total_services = await self._service_repo.count()
        active_services = len(await self._service_repo.find_by_status(ServiceStatus.ACTIVE))
        inactive_services = len(await self._service_repo.find_by_status(ServiceStatus.INACTIVE))

        # Get service type distribution
        api_services = len(await self._service_repo.find_by_type(ServiceType.API))
        database_services = len(await self._service_repo.find_by_type(ServiceType.DATABASE))
        integration_services = len(await self._service_repo.find_by_type(ServiceType.INTEGRATION))

        return {
            "total_services": total_services,
            "active_services": active_services,
            "inactive_services": inactive_services,
            "service_types": {
                "api": api_services,
                "database": database_services,
                "integration": integration_services
            },
            "health_score": (active_services / total_services * 100) if total_services > 0 else 0
        }

    async def get_services_by_technology(self, technology: str) -> List[ExternalService]:
        """Find all services using a specific technology."""
        return await self._service_repo.find_services_by_technology(technology)

    async def get_services_by_topic(self, topic: str) -> List[ExternalService]:
        """Find all services related to a topic."""
        return await self._service_repo.find_services_by_topic(topic)

    async def get_recent_service_activity(self, service_id: str) -> Dict[str, Any]:
        """Get recent activity summary for a service."""
        service = await self._service_repo.find_by_id(service_id)
        if not service:
            return {}

        recent_docs = await self._document_repo.find_recent_by_service_and_type(service_id, "github_pr", 5)

        return {
            "service_id": service_id,
            "last_confluence": service.last_confluence_document,
            "last_jira": service.last_jira_ticket,
            "last_github_pr": service.last_github_pr,
            "recent_activity": [
                {
                    "type": doc.document_type,
                    "document_id": doc.document_id,
                    "last_updated": doc.last_updated.isoformat() if doc.last_updated else None
                }
                for doc in recent_docs
            ]
        }

    async def detect_services_in_document(self, document_content: str, document_metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """Detect service mentions in document content and metadata.

        This method analyzes document content to find references to services
        that are registered in the external service store.

        Args:
            document_content: The full text content of the document
            document_metadata: Optional document metadata

        Returns:
            List of service IDs that were detected in the document
        """
        detected_services = []

        # Get all registered services for pattern matching
        all_services = await self._service_repo.list_all_services(limit=1000)
        service_names = {service.name: service.id for service in all_services}
        service_display_names = {service.display_name: service.id for service in all_services if service.display_name}

        # Create combined lookup dictionary
        service_lookup = {**service_names, **service_display_names}

        # Search patterns for service detection
        content_lower = document_content.lower()

        for service_name, service_id in service_lookup.items():
            # Exact matches first
            if service_name.lower() in content_lower:
                if service_id not in detected_services:
                    detected_services.append(service_id)
                continue

            # Check metadata for service references
            if document_metadata:
                metadata_str = str(document_metadata).lower()
                if service_name.lower() in metadata_str:
                    if service_id not in detected_services:
                        detected_services.append(service_id)

        return detected_services

    async def create_document_service_relationships(
        self,
        document_id: str,
        document_content: str,
        document_metadata: Optional[Dict[str, Any]] = None,
        document_type: str = "unknown"
    ) -> Dict[str, Any]:
        """Automatically create bidirectional relationships between a document and detected services.

        This method is called during document ingestion to establish relationships
        between documents and services mentioned within them.

        Args:
            document_id: Unique identifier of the document
            document_content: Full text content of the document
            document_metadata: Optional document metadata
            document_type: Type of document (confluence, jira, github_pr, etc.)

        Returns:
            Dictionary with relationship creation results
        """
        detected_service_ids = await self.detect_services_in_document(document_content, document_metadata)

        created_relationships = []

        for service_id in detected_service_ids:
            try:
                # Create document relationship from service perspective
                doc_rel = await self.add_service_document(
                    service_id=service_id,
                    document_id=document_id,
                    document_type=document_type,
                    relationship_type="reference",
                    description=f"Referenced in {document_type} document"
                )

                created_relationships.append({
                    'service_id': service_id,
                    'document_id': document_id,
                    'relationship_type': 'service_to_document',
                    'relationship_id': doc_rel.id
                })

                # Update service activity if it's a recent document type
                if document_type in ['confluence', 'jira', 'github_pr']:
                    await self.update_service_activity(service_id, document_type, document_id)

            except ValueError:
                # Relationship might already exist, skip
                continue

        return {
            'document_id': document_id,
            'document_type': document_type,
            'detected_services': len(detected_service_ids),
            'relationships_created': len(created_relationships),
            'service_ids': detected_service_ids,
            'relationships': created_relationships
        }

    async def get_document_services(self, document_id: str) -> List[ExternalService]:
        """Get all services related to a specific document.

        Args:
            document_id: Document identifier

        Returns:
            List of services related to the document
        """
        relationships = await self._document_repo.find_by_document(document_id)

        services = []
        for rel in relationships:
            service = await self._service_repo.find_by_id(rel.service_id)
            if service:
                services.append(service)

        return services

    async def get_service_documents_paginated(
        self,
        service_id: str,
        document_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get paginated list of documents for a service.

        Args:
            service_id: Service identifier
            document_type: Optional filter by document type
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            Dictionary with documents and pagination info
        """
        if document_type:
            documents = await self._document_repo.find_recent_by_service_and_type(service_id, document_type, limit)
        else:
            all_docs = await self._document_repo.find_by_service(service_id)
            documents = all_docs[offset:offset + limit]

        return {
            'service_id': service_id,
            'document_type': document_type,
            'documents': [doc.__dict__ for doc in documents],
            'total': len(documents),
            'limit': limit,
            'offset': offset
        }

    async def sync_document_relationships(
        self,
        document_id: str,
        service_ids: List[str],
        document_type: str = "unknown",
        relationship_type: str = "reference"
    ) -> Dict[str, Any]:
        """Synchronize document-service relationships from an external source.

        This method is useful for bulk synchronization or when relationships
        are established from other parts of the system.

        Args:
            document_id: Document identifier
            service_ids: List of service IDs to relate
            document_type: Type of document
            relationship_type: Type of relationship

        Returns:
            Synchronization results
        """
        results = {
            'document_id': document_id,
            'total_services': len(service_ids),
            'successful_relationships': 0,
            'failed_relationships': 0,
            'errors': []
        }

        for service_id in service_ids:
            try:
                # Verify service exists
                service = await self._service_repo.find_by_id(service_id)
                if not service:
                    results['errors'].append(f"Service {service_id} not found")
                    results['failed_relationships'] += 1
                    continue

                # Create the relationship
                await self.add_service_document(
                    service_id=service_id,
                    document_id=document_id,
                    document_type=document_type,
                    relationship_type=relationship_type,
                    description=f"Synchronized relationship from {document_type}"
                )

                results['successful_relationships'] += 1

            except Exception as e:
                results['errors'].append(f"Failed to create relationship for service {service_id}: {str(e)}")
                results['failed_relationships'] += 1

        return results

    async def get_relationship_health_check(self) -> Dict[str, Any]:
        """Perform a health check on service-document relationships.

        Returns statistics about relationship consistency and potential issues.
        """
        # Get all services and their document relationships
        services = await self._service_repo.list_all_services(limit=1000)
        documents = await self._document_repo.list_all_documents(limit=10000)

        # Analyze relationship health
        service_count = len(services)
        document_count = len(documents)

        # Count relationships by type
        relationship_stats = {}
        for doc in documents:
            rel_type = doc.relationship_type
            if rel_type not in relationship_stats:
                relationship_stats[rel_type] = 0
            relationship_stats[rel_type] += 1

        # Check for orphaned relationships
        orphaned_docs = 0
        for doc in documents:
            service = await self._service_repo.find_by_id(doc.service_id)
            if not service:
                orphaned_docs += 1

        return {
            'total_services': service_count,
            'total_document_relationships': document_count,
            'relationship_types': relationship_stats,
            'orphaned_relationships': orphaned_docs,
            'health_score': ((document_count - orphaned_docs) / max(document_count, 1)) * 100,
            'average_relationships_per_service': document_count / max(service_count, 1)
        }
