"""External Service entity for the External Service Store.

This module defines the ExternalService entity and related domain objects
for tracking external services, their metadata, relationships, and technical details.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum


class ServiceStatus(Enum):
    """Status of an external service."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"


class ServiceType(Enum):
    """Type/category of external service."""
    API = "api"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    CACHE = "cache"
    STORAGE = "storage"
    AUTHENTICATION = "authentication"
    MONITORING = "monitoring"
    LOGGING = "logging"
    NOTIFICATION = "notification"
    ANALYTICS = "analytics"
    INTEGRATION = "integration"
    OTHER = "other"


@dataclass
class ServiceEndpoint:
    """Represents an API endpoint for an external service."""
    id: str = ""
    path: str = ""
    method: str = "GET"
    description: str = ""
    request_contract: Dict[str, Any] = field(default_factory=dict)
    response_contract: Dict[str, Any] = field(default_factory=dict)
    response_types: List[str] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    authentication_required: bool = False
    rate_limit: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate endpoint data."""
        if not self.path.startswith('/'):
            self.path = f'/{self.path}'
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ServiceDependency:
    """Represents a dependency relationship between services."""
    id: str = ""
    dependent_service_id: str = ""
    dependency_service_id: str = ""
    dependency_type: str = "runtime"  # runtime, build, optional, etc.
    version_constraint: Optional[str] = None
    description: str = ""
    is_required: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate dependency data."""
        if not self.dependent_service_id:
            raise ValueError("Dependent service ID cannot be empty")
        if not self.dependency_service_id:
            raise ValueError("Dependency service ID cannot be empty")
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ServiceDocument:
    """Represents a relationship between a service and a document."""
    id: str = ""
    service_id: str = ""
    document_id: str = ""
    document_type: str = ""  # confluence, jira, github_pr, readme, etc.
    relationship_type: str = "reference"  # reference, implements, documents, etc.
    last_updated: Optional[datetime] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate document relationship."""
        if not self.service_id:
            raise ValueError("Service ID cannot be empty")
        if not self.document_id:
            raise ValueError("Document ID cannot be empty")
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ServiceUser:
    """Represents a relationship between a service and a user."""
    id: str = ""
    service_id: str = ""
    user_id: str = ""
    relationship_type: str = "maintainer"  # maintainer, contributor, user, etc.
    role: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    last_interaction: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate user relationship."""
        if not self.service_id:
            raise ValueError("Service ID cannot be empty")
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ServiceTopic:
    """Represents a relationship between a service and a topic."""
    id: str = ""
    service_id: str = ""
    topic: str = ""
    relevance_score: int = 50  # 0-100, how relevant this topic is to the service
    tags: List[str] = field(default_factory=list)
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate topic relationship."""
        if not self.service_id:
            raise ValueError("Service ID cannot be empty")
        if not self.topic:
            raise ValueError("Topic cannot be empty")
        self.relevance_score = max(0, min(100, self.relevance_score))
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ExternalService:
    """Main entity representing an external service in the ecosystem."""
    id: str = ""
    name: str = ""
    display_name: str = ""
    description: str = ""
    summary: str = ""
    service_type: ServiceType = ServiceType.OTHER
    status: ServiceStatus = ServiceStatus.ACTIVE

    # Version and release information
    version: str = "1.0.0"
    latest_release: Optional[str] = None
    release_date: Optional[datetime] = None

    # Technical details
    technologies: List[str] = field(default_factory=list)
    run_requirements: Dict[str, Any] = field(default_factory=dict)
    base_url: Optional[str] = None
    port: Optional[int] = None
    health_endpoint: Optional[str] = None

    # Relationships
    endpoints: List[ServiceEndpoint] = field(default_factory=list)
    dependencies: List[ServiceDependency] = field(default_factory=list)
    documents: List[ServiceDocument] = field(default_factory=list)
    users: List[ServiceUser] = field(default_factory=list)
    topics: List[ServiceTopic] = field(default_factory=list)

    # Recent activity
    last_confluence_document: Optional[str] = None
    last_jira_ticket: Optional[str] = None
    last_github_pr: Optional[str] = None

    # Data contracts
    data_contracts: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    owner: Optional[str] = None
    maintainers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # System tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate service data after initialization."""
        if not self.name:
            raise ValueError("Service name cannot be empty")
        if not self.display_name:
            self.display_name = self.name.replace('-', ' ').replace('_', ' ').title()

        # Ensure version follows semantic versioning
        if not self._is_valid_version(self.version):
            raise ValueError(f"Invalid version format: {self.version}")

        self.updated_at = datetime.now(timezone.utc)

    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning."""
        import re
        # Simple semver pattern: x.y.z
        return bool(re.match(r'^\d+\.\d+\.\d+$', version))

    def update_version(self, new_version: str) -> None:
        """Update service version and release date."""
        if not self._is_valid_version(new_version):
            raise ValueError(f"Invalid version format: {new_version}")

        self.version = new_version
        self.release_date = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def add_endpoint(self, endpoint: ServiceEndpoint) -> None:
        """Add an endpoint to the service."""
        # Check for duplicate paths/methods
        for existing in self.endpoints:
            if existing.path == endpoint.path and existing.method == endpoint.method:
                raise ValueError(f"Endpoint {endpoint.method} {endpoint.path} already exists")

        self.endpoints.append(endpoint)
        self.updated_at = datetime.now(timezone.utc)

    def remove_endpoint(self, endpoint_id: str) -> bool:
        """Remove an endpoint from the service."""
        for i, endpoint in enumerate(self.endpoints):
            if endpoint.id == endpoint_id:
                self.endpoints.pop(i)
                self.updated_at = datetime.now(timezone.utc)
                return True
        return False

    def add_dependency(self, dependency: ServiceDependency) -> None:
        """Add a service dependency."""
        # Check for duplicate dependencies
        for existing in self.dependencies:
            if (existing.dependent_service_id == dependency.dependent_service_id and
                existing.dependency_service_id == dependency.dependency_service_id):
                raise ValueError("Dependency relationship already exists")

        self.dependencies.append(dependency)
        self.updated_at = datetime.now(timezone.utc)

    def add_document_relationship(self, document: ServiceDocument) -> None:
        """Add a document relationship."""
        # Update last document references based on type
        if document.document_type == "confluence":
            self.last_confluence_document = document.document_id
        elif document.document_type == "jira":
            self.last_jira_ticket = document.document_id
        elif document.document_type == "github_pr":
            self.last_github_pr = document.document_id

        self.documents.append(document)
        self.updated_at = datetime.now(timezone.utc)

    def add_user_relationship(self, user: ServiceUser) -> None:
        """Add a user relationship."""
        self.users.append(user)
        self.updated_at = datetime.now(timezone.utc)

    def add_topic_relationship(self, topic: ServiceTopic) -> None:
        """Add a topic relationship."""
        # Check for duplicate topics
        for existing in self.topics:
            if existing.topic == topic.topic:
                raise ValueError(f"Topic '{topic.topic}' relationship already exists")

        self.topics.append(topic)
        self.updated_at = datetime.now(timezone.utc)

    def update_activity(self, activity_type: str, reference: str) -> None:
        """Update service activity tracking."""
        if activity_type == "confluence":
            self.last_confluence_document = reference
        elif activity_type == "jira":
            self.last_jira_ticket = reference
        elif activity_type == "github_pr":
            self.last_github_pr = reference

        self.updated_at = datetime.now(timezone.utc)

    def get_active_endpoints(self) -> List[ServiceEndpoint]:
        """Get all active endpoints."""
        return [ep for ep in self.endpoints if ep.id]  # All endpoints with IDs are considered active

    def get_dependencies_by_type(self, dep_type: str) -> List[ServiceDependency]:
        """Get dependencies filtered by type."""
        return [dep for dep in self.dependencies if dep.dependency_type == dep_type]

    def get_documents_by_type(self, doc_type: str) -> List[ServiceDocument]:
        """Get documents filtered by type."""
        return [doc for doc in self.documents if doc.document_type == doc_type]

    def get_users_by_relationship(self, rel_type: str) -> List[ServiceUser]:
        """Get users filtered by relationship type."""
        return [user for user in self.users if user.relationship_type == rel_type]

    def get_top_topics(self, limit: int = 5) -> List[ServiceTopic]:
        """Get top topics by relevance score."""
        sorted_topics = sorted(self.topics, key=lambda t: t.relevance_score, reverse=True)
        return sorted_topics[:limit]
