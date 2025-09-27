"""SQLite implementation of External Service repositories.

This module provides SQLite-based repository implementations for managing
external services and their relationships.
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.entities.external_service import (
    ExternalService, ServiceEndpoint, ServiceDependency,
    ServiceDocument, ServiceUser, ServiceTopic,
    ServiceStatus, ServiceType
)
from ...domain.repositories.external_service_repository import (
    ExternalServiceRepository, ServiceEndpointRepository,
    ServiceDependencyRepository, ServiceDocumentRepository,
    ServiceUserRepository, ServiceTopicRepository
)


class SQLiteExternalServiceRepository(ExternalServiceRepository):
    """SQLite implementation of ExternalServiceRepository."""

    def __init__(self, db_path: str = "external_service_store.db"):
        """Initialize the repository with database connection."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Main services table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS external_services (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    summary TEXT,
                    service_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    version TEXT NOT NULL,
                    latest_release TEXT,
                    release_date TEXT,
                    technologies TEXT NOT NULL,  -- JSON array
                    run_requirements TEXT NOT NULL,  -- JSON object
                    base_url TEXT,
                    port INTEGER,
                    health_endpoint TEXT,
                    last_confluence_document TEXT,
                    last_jira_ticket TEXT,
                    last_github_pr TEXT,
                    data_contracts TEXT NOT NULL,  -- JSON object
                    owner TEXT,
                    maintainers TEXT NOT NULL,  -- JSON array
                    tags TEXT NOT NULL,  -- JSON array
                    metadata TEXT NOT NULL,  -- JSON object
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Endpoints table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service_endpoints (
                    id TEXT PRIMARY KEY,
                    service_id TEXT NOT NULL,
                    path TEXT NOT NULL,
                    method TEXT NOT NULL,
                    description TEXT,
                    request_contract TEXT NOT NULL,  -- JSON object
                    response_contract TEXT NOT NULL,  -- JSON object
                    response_types TEXT NOT NULL,  -- JSON array
                    parameters TEXT NOT NULL,  -- JSON array
                    authentication_required BOOLEAN NOT NULL,
                    rate_limit TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(service_id) REFERENCES external_services(id) ON DELETE CASCADE,
                    UNIQUE(service_id, path, method)
                )
            """)

            # Dependencies table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service_dependencies (
                    id TEXT PRIMARY KEY,
                    dependent_service_id TEXT NOT NULL,
                    dependency_service_id TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    version_constraint TEXT,
                    description TEXT,
                    is_required BOOLEAN NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(dependent_service_id) REFERENCES external_services(id) ON DELETE CASCADE,
                    FOREIGN KEY(dependency_service_id) REFERENCES external_services(id) ON DELETE CASCADE
                )
            """)

            # Document relationships table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service_documents (
                    id TEXT PRIMARY KEY,
                    service_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    last_updated TEXT,
                    description TEXT,
                    tags TEXT NOT NULL,  -- JSON array
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(service_id) REFERENCES external_services(id) ON DELETE CASCADE
                )
            """)

            # User relationships table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service_users (
                    id TEXT PRIMARY KEY,
                    service_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    role TEXT,
                    permissions TEXT NOT NULL,  -- JSON array
                    last_interaction TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(service_id) REFERENCES external_services(id) ON DELETE CASCADE,
                    UNIQUE(service_id, user_id)
                )
            """)

            # Topic relationships table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service_topics (
                    id TEXT PRIMARY KEY,
                    service_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    relevance_score INTEGER NOT NULL,
                    tags TEXT NOT NULL,  -- JSON array
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(service_id) REFERENCES external_services(id) ON DELETE CASCADE,
                    UNIQUE(service_id, topic)
                )
            """)

            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_services_name ON external_services(name)",
                "CREATE INDEX IF NOT EXISTS idx_services_type ON external_services(service_type)",
                "CREATE INDEX IF NOT EXISTS idx_services_status ON external_services(status)",
                "CREATE INDEX IF NOT EXISTS idx_services_technologies ON external_services(technologies)",
                "CREATE INDEX IF NOT EXISTS idx_endpoints_service ON service_endpoints(service_id)",
                "CREATE INDEX IF NOT EXISTS idx_dependencies_dependent ON service_dependencies(dependent_service_id)",
                "CREATE INDEX IF NOT EXISTS idx_dependencies_dependency ON service_dependencies(dependency_service_id)",
                "CREATE INDEX IF NOT EXISTS idx_documents_service ON service_documents(service_id)",
                "CREATE INDEX IF NOT EXISTS idx_documents_type ON service_documents(document_type)",
                "CREATE INDEX IF NOT EXISTS idx_users_service ON service_users(service_id)",
                "CREATE INDEX IF NOT EXISTS idx_users_user ON service_users(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_topics_service ON service_topics(service_id)",
                "CREATE INDEX IF NOT EXISTS idx_topics_topic ON service_topics(topic)"
            ]

            for index in indexes:
                conn.execute(index)

            conn.commit()

    def _service_from_row(self, row) -> ExternalService:
        """Convert database row to ExternalService entity."""
        return ExternalService(
            id=row[0],
            name=row[1],
            display_name=row[2],
            description=row[3] or "",
            summary=row[4] or "",
            service_type=ServiceType(row[5]),
            status=ServiceStatus(row[6]),
            version=row[7],
            latest_release=row[8],
            release_date=datetime.fromisoformat(row[9]) if row[9] else None,
            technologies=json.loads(row[10]) if row[10] else [],
            run_requirements=json.loads(row[11]) if row[11] else {},
            base_url=row[12],
            port=row[13],
            health_endpoint=row[14],
            last_confluence_document=row[15],
            last_jira_ticket=row[16],
            last_github_pr=row[17],
            data_contracts=json.loads(row[18]) if row[18] else {},
            owner=row[19],
            maintainers=json.loads(row[20]) if row[20] else [],
            tags=json.loads(row[21]) if row[21] else [],
            metadata=json.loads(row[22]) if row[22] else {},
            created_at=datetime.fromisoformat(row[23]),
            updated_at=datetime.fromisoformat(row[24])
        )

    async def save(self, service: ExternalService) -> None:
        """Save an external service to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO external_services (
                    id, name, display_name, description, summary, service_type, status,
                    version, latest_release, release_date, technologies, run_requirements,
                    base_url, port, health_endpoint, last_confluence_document,
                    last_jira_ticket, last_github_pr, data_contracts, owner, maintainers,
                    tags, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                service.id, service.name, service.display_name, service.description,
                service.summary, service.service_type.value, service.status.value,
                service.version, service.latest_release,
                service.release_date.isoformat() if service.release_date else None,
                json.dumps(service.technologies), json.dumps(service.run_requirements),
                service.base_url, service.port, service.health_endpoint,
                service.last_confluence_document, service.last_jira_ticket, service.last_github_pr,
                json.dumps(service.data_contracts), service.owner,
                json.dumps(service.maintainers), json.dumps(service.tags),
                json.dumps(service.metadata), service.created_at.isoformat(),
                service.updated_at.isoformat()
            ))
            conn.commit()

    async def find_by_id(self, service_id: str) -> Optional[ExternalService]:
        """Find service by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM external_services WHERE id = ?", (service_id,))
            row = cursor.fetchone()
            return self._service_from_row(row) if row else None

    async def find_by_name(self, name: str) -> Optional[ExternalService]:
        """Find service by name."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM external_services WHERE name = ?", (name,))
            row = cursor.fetchone()
            return self._service_from_row(row) if row else None

    async def find_by_status(self, status: ServiceStatus) -> List[ExternalService]:
        """Find services by status."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM external_services WHERE status = ?", (status.value,))
            return [self._service_from_row(row) for row in cursor.fetchall()]

    async def find_by_type(self, service_type: ServiceType) -> List[ExternalService]:
        """Find services by type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM external_services WHERE service_type = ?", (service_type.value,))
            return [self._service_from_row(row) for row in cursor.fetchall()]

    async def find_services_by_technology(self, technology: str) -> List[ExternalService]:
        """Find services using a specific technology."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM external_services WHERE technologies LIKE ?", (f'%{technology}%',))
            services = []
            for row in cursor.fetchall():
                service = self._service_from_row(row)
                if technology in service.technologies:
                    services.append(service)
            return services

    async def find_services_by_topic(self, topic: str) -> List[ExternalService]:
        """Find services related to a topic."""
        # This requires joining with service_topics table
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT es.* FROM external_services es
                JOIN service_topics st ON es.id = st.service_id
                WHERE st.topic = ?
            """, (topic,))
            return [self._service_from_row(row) for row in cursor.fetchall()]

    async def find_services_by_user(self, user_id: str) -> List[ExternalService]:
        """Find services related to a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT es.* FROM external_services es
                JOIN service_users su ON es.id = su.service_id
                WHERE su.user_id = ?
            """, (user_id,))
            return [self._service_from_row(row) for row in cursor.fetchall()]

    async def search_services(self, query: str, limit: int = 50) -> List[ExternalService]:
        """Search services by name, description, or tags."""
        query_lower = f"%{query.lower()}%"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM external_services
                WHERE LOWER(name) LIKE ? OR LOWER(display_name) LIKE ? OR LOWER(description) LIKE ? OR tags LIKE ?
                LIMIT ?
            """, (query_lower, query_lower, query_lower, query_lower, limit))
            return [self._service_from_row(row) for row in cursor.fetchall()]

    async def list_all_services(self, limit: int = 100, offset: int = 0) -> List[ExternalService]:
        """List all services with pagination."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM external_services LIMIT ? OFFSET ?", (limit, offset))
            return [self._service_from_row(row) for row in cursor.fetchall()]

    async def update(self, service: ExternalService) -> None:
        """Update an existing service."""
        await self.save(service)

    async def delete(self, service_id: str) -> bool:
        """Delete a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM external_services WHERE id = ?", (service_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def exists(self, service_id: str) -> bool:
        """Check if service exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM external_services WHERE id = ? LIMIT 1", (service_id,))
            return cursor.fetchone() is not None

    async def count(self) -> int:
        """Count total services."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM external_services")
            return cursor.fetchone()[0]


class SQLiteServiceEndpointRepository(ServiceEndpointRepository):
    """SQLite implementation of ServiceEndpointRepository."""

    def __init__(self, db_path: str = "external_service_store.db"):
        """Initialize the repository."""
        self.db_path = db_path

    def _endpoint_from_row(self, row) -> ServiceEndpoint:
        """Convert database row to ServiceEndpoint entity."""
        return ServiceEndpoint(
            id=row[0],
            path=row[2],
            method=row[3],
            description=row[4] or "",
            request_contract=json.loads(row[5]) if row[5] else {},
            response_contract=json.loads(row[6]) if row[6] else {},
            response_types=json.loads(row[7]) if row[7] else [],
            parameters=json.loads(row[8]) if row[8] else [],
            authentication_required=bool(row[9]),
            rate_limit=row[10],
            created_at=datetime.fromisoformat(row[11]),
            updated_at=datetime.fromisoformat(row[12])
        )

    async def save(self, endpoint: ServiceEndpoint) -> None:
        """Save an endpoint."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO service_endpoints (
                    id, service_id, path, method, description, request_contract,
                    response_contract, response_types, parameters, authentication_required,
                    rate_limit, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                endpoint.id, getattr(endpoint, 'service_id', ''),
                endpoint.path, endpoint.method, endpoint.description,
                json.dumps(endpoint.request_contract), json.dumps(endpoint.response_contract),
                json.dumps(endpoint.response_types), json.dumps(endpoint.parameters),
                endpoint.authentication_required, endpoint.rate_limit,
                endpoint.created_at.isoformat(), endpoint.updated_at.isoformat()
            ))
            conn.commit()

    async def find_by_id(self, endpoint_id: str) -> Optional[ServiceEndpoint]:
        """Find endpoint by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_endpoints WHERE id = ?", (endpoint_id,))
            row = cursor.fetchone()
            return self._endpoint_from_row(row) if row else None

    async def find_by_service(self, service_id: str) -> List[ServiceEndpoint]:
        """Find all endpoints for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_endpoints WHERE service_id = ?", (service_id,))
            return [self._endpoint_from_row(row) for row in cursor.fetchall()]

    async def find_by_path_and_method(self, service_id: str, path: str, method: str) -> Optional[ServiceEndpoint]:
        """Find endpoint by service, path, and method."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM service_endpoints
                WHERE service_id = ? AND path = ? AND method = ?
            """, (service_id, path, method))
            row = cursor.fetchone()
            return self._endpoint_from_row(row) if row else None

    async def update(self, endpoint: ServiceEndpoint) -> None:
        """Update an endpoint."""
        await self.save(endpoint)

    async def delete(self, endpoint_id: str) -> bool:
        """Delete an endpoint."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_endpoints WHERE id = ?", (endpoint_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def delete_by_service(self, service_id: str) -> int:
        """Delete all endpoints for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_endpoints WHERE service_id = ?", (service_id,))
            conn.commit()
            return cursor.rowcount


class SQLiteServiceDependencyRepository(ServiceDependencyRepository):
    """SQLite implementation of ServiceDependencyRepository."""

    def __init__(self, db_path: str = "external_service_store.db"):
        """Initialize the repository."""
        self.db_path = db_path

    def _dependency_from_row(self, row) -> ServiceDependency:
        """Convert database row to ServiceDependency entity."""
        return ServiceDependency(
            id=row[0],
            dependent_service_id=row[1],
            dependency_service_id=row[2],
            dependency_type=row[3],
            version_constraint=row[4],
            description=row[5] or "",
            is_required=bool(row[6]),
            created_at=datetime.fromisoformat(row[7]),
            updated_at=datetime.fromisoformat(row[8])
        )

    async def save(self, dependency: ServiceDependency) -> None:
        """Save a dependency."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO service_dependencies (
                    id, dependent_service_id, dependency_service_id, dependency_type,
                    version_constraint, description, is_required, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dependency.id, dependency.dependent_service_id, dependency.dependency_service_id,
                dependency.dependency_type, dependency.version_constraint, dependency.description,
                dependency.is_required, dependency.created_at.isoformat(),
                dependency.updated_at.isoformat()
            ))
            conn.commit()

    async def find_by_id(self, dependency_id: str) -> Optional[ServiceDependency]:
        """Find dependency by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_dependencies WHERE id = ?", (dependency_id,))
            row = cursor.fetchone()
            return self._dependency_from_row(row) if row else None

    async def find_dependencies_by_service(self, service_id: str) -> List[ServiceDependency]:
        """Find all dependencies for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_dependencies WHERE dependent_service_id = ?", (service_id,))
            return [self._dependency_from_row(row) for row in cursor.fetchall()]

    async def find_dependents_of_service(self, service_id: str) -> List[ServiceDependency]:
        """Find all services that depend on the given service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_dependencies WHERE dependency_service_id = ?", (service_id,))
            return [self._dependency_from_row(row) for row in cursor.fetchall()]

    async def find_by_type(self, dependency_type: str) -> List[ServiceDependency]:
        """Find dependencies by type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_dependencies WHERE dependency_type = ?", (dependency_type,))
            return [self._dependency_from_row(row) for row in cursor.fetchall()]

    async def update(self, dependency: ServiceDependency) -> None:
        """Update a dependency."""
        await self.save(dependency)

    async def delete(self, dependency_id: str) -> bool:
        """Delete a dependency."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_dependencies WHERE id = ?", (dependency_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def delete_by_service(self, service_id: str) -> int:
        """Delete all dependencies for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_dependencies WHERE dependent_service_id = ?", (service_id,))
            conn.commit()
            return cursor.rowcount


class SQLiteServiceDocumentRepository(ServiceDocumentRepository):
    """SQLite implementation of ServiceDocumentRepository."""

    def __init__(self, db_path: str = "external_service_store.db"):
        """Initialize the repository."""
        self.db_path = db_path

    def _document_from_row(self, row) -> ServiceDocument:
        """Convert database row to ServiceDocument entity."""
        return ServiceDocument(
            id=row[0],
            service_id=row[1],
            document_id=row[2],
            document_type=row[3],
            relationship_type=row[4],
            last_updated=datetime.fromisoformat(row[5]) if row[5] else None,
            description=row[6] or "",
            tags=json.loads(row[7]) if row[7] else [],
            created_at=datetime.fromisoformat(row[8]),
            updated_at=datetime.fromisoformat(row[9])
        )

    async def save(self, document: ServiceDocument) -> None:
        """Save a document relationship."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO service_documents (
                    id, service_id, document_id, document_type, relationship_type,
                    last_updated, description, tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document.id, document.service_id, document.document_id, document.document_type,
                document.relationship_type,
                document.last_updated.isoformat() if document.last_updated else None,
                document.description, json.dumps(document.tags),
                document.created_at.isoformat(), document.updated_at.isoformat()
            ))
            conn.commit()

    async def find_by_id(self, document_id: str) -> Optional[ServiceDocument]:
        """Find document relationship by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_documents WHERE id = ?", (document_id,))
            row = cursor.fetchone()
            return self._document_from_row(row) if row else None

    async def find_by_service(self, service_id: str) -> List[ServiceDocument]:
        """Find all documents for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_documents WHERE service_id = ?", (service_id,))
            return [self._document_from_row(row) for row in cursor.fetchall()]

    async def find_by_document(self, document_id: str) -> List[ServiceDocument]:
        """Find all services related to a document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_documents WHERE document_id = ?", (document_id,))
            return [self._document_from_row(row) for row in cursor.fetchall()]

    async def find_by_type(self, document_type: str) -> List[ServiceDocument]:
        """Find documents by type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_documents WHERE document_type = ?", (document_type,))
            return [self._document_from_row(row) for row in cursor.fetchall()]

    async def find_recent_by_service_and_type(self, service_id: str, doc_type: str, limit: int = 1) -> List[ServiceDocument]:
        """Find recent documents of specific type for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM service_documents
                WHERE service_id = ? AND document_type = ?
                ORDER BY last_updated DESC NULLS LAST, updated_at DESC
                LIMIT ?
            """, (service_id, doc_type, limit))
            return [self._document_from_row(row) for row in cursor.fetchall()]

    async def update(self, document: ServiceDocument) -> None:
        """Update a document relationship."""
        await self.save(document)

    async def delete(self, document_id: str) -> bool:
        """Delete a document relationship."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_documents WHERE id = ?", (document_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def delete_by_service(self, service_id: str) -> int:
        """Delete all document relationships for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_documents WHERE service_id = ?", (service_id,))
            conn.commit()
            return cursor.rowcount

    async def delete_by_document(self, document_id: str) -> int:
        """Delete all service relationships for a document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_documents WHERE document_id = ?", (document_id,))
            conn.commit()
            return cursor.rowcount

    async def list_all_documents(self, limit: int = 1000) -> List[ServiceDocument]:
        """List all document relationships with optional limit."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_documents LIMIT ?", (limit,))
            return [self._document_from_row(row) for row in cursor.fetchall()]


class SQLiteServiceUserRepository(ServiceUserRepository):
    """SQLite implementation of ServiceUserRepository."""

    def __init__(self, db_path: str = "external_service_store.db"):
        """Initialize the repository."""
        self.db_path = db_path

    def _user_from_row(self, row) -> ServiceUser:
        """Convert database row to ServiceUser entity."""
        return ServiceUser(
            id=row[0],
            service_id=row[1],
            user_id=row[2],
            relationship_type=row[3],
            role=row[4],
            permissions=json.loads(row[5]) if row[5] else [],
            last_interaction=datetime.fromisoformat(row[6]) if row[6] else None,
            created_at=datetime.fromisoformat(row[7]),
            updated_at=datetime.fromisoformat(row[8])
        )

    async def save(self, user: ServiceUser) -> None:
        """Save a user relationship."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO service_users (
                    id, service_id, user_id, relationship_type, role, permissions,
                    last_interaction, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.id, user.service_id, user.user_id, user.relationship_type,
                user.role, json.dumps(user.permissions),
                user.last_interaction.isoformat() if user.last_interaction else None,
                user.created_at.isoformat(), user.updated_at.isoformat()
            ))
            conn.commit()

    async def find_by_id(self, user_id: str) -> Optional[ServiceUser]:
        """Find user relationship by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return self._user_from_row(row) if row else None

    async def find_by_service(self, service_id: str) -> List[ServiceUser]:
        """Find all users for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_users WHERE service_id = ?", (service_id,))
            return [self._user_from_row(row) for row in cursor.fetchall()]

    async def find_by_user(self, user_id: str) -> List[ServiceUser]:
        """Find all services for a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_users WHERE user_id = ?", (user_id,))
            return [self._user_from_row(row) for row in cursor.fetchall()]

    async def find_by_relationship_type(self, relationship_type: str) -> List[ServiceUser]:
        """Find user relationships by type."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_users WHERE relationship_type = ?", (relationship_type,))
            return [self._user_from_row(row) for row in cursor.fetchall()]

    async def find_maintainers_by_service(self, service_id: str) -> List[ServiceUser]:
        """Find maintainers for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM service_users
                WHERE service_id = ? AND relationship_type = 'maintainer'
            """, (service_id,))
            return [self._user_from_row(row) for row in cursor.fetchall()]

    async def update(self, user: ServiceUser) -> None:
        """Update a user relationship."""
        await self.save(user)

    async def delete(self, user_id: str) -> bool:
        """Delete a user relationship."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def delete_by_service(self, service_id: str) -> int:
        """Delete all user relationships for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_users WHERE service_id = ?", (service_id,))
            conn.commit()
            return cursor.rowcount

    async def delete_by_user(self, user_id: str) -> int:
        """Delete all service relationships for a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_users WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount


class SQLiteServiceTopicRepository(ServiceTopicRepository):
    """SQLite implementation of ServiceTopicRepository."""

    def __init__(self, db_path: str = "external_service_store.db"):
        """Initialize the repository."""
        self.db_path = db_path

    def _topic_from_row(self, row) -> ServiceTopic:
        """Convert database row to ServiceTopic entity."""
        return ServiceTopic(
            id=row[0],
            service_id=row[1],
            topic=row[2],
            relevance_score=row[3],
            tags=json.loads(row[4]) if row[4] else [],
            description=row[5] or "",
            created_at=datetime.fromisoformat(row[6]),
            updated_at=datetime.fromisoformat(row[7])
        )

    async def save(self, topic: ServiceTopic) -> None:
        """Save a topic relationship."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO service_topics (
                    id, service_id, topic, relevance_score, tags, description, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                topic.id, topic.service_id, topic.topic, topic.relevance_score,
                json.dumps(topic.tags), topic.description,
                topic.created_at.isoformat(), topic.updated_at.isoformat()
            ))
            conn.commit()

    async def find_by_id(self, topic_id: str) -> Optional[ServiceTopic]:
        """Find topic relationship by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_topics WHERE id = ?", (topic_id,))
            row = cursor.fetchone()
            return self._topic_from_row(row) if row else None

    async def find_by_service(self, service_id: str) -> List[ServiceTopic]:
        """Find all topics for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_topics WHERE service_id = ?", (service_id,))
            return [self._topic_from_row(row) for row in cursor.fetchall()]

    async def find_by_topic(self, topic: str) -> List[ServiceTopic]:
        """Find all services related to a topic."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_topics WHERE topic = ?", (topic,))
            return [self._topic_from_row(row) for row in cursor.fetchall()]

    async def find_by_relevance_score(self, min_score: int = 50) -> List[ServiceTopic]:
        """Find topic relationships above minimum relevance score."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM service_topics WHERE relevance_score >= ?", (min_score,))
            return [self._topic_from_row(row) for row in cursor.fetchall()]

    async def update(self, topic: ServiceTopic) -> None:
        """Update a topic relationship."""
        await self.save(topic)

    async def delete(self, topic_id: str) -> bool:
        """Delete a topic relationship."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_topics WHERE id = ?", (topic_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def delete_by_service(self, service_id: str) -> int:
        """Delete all topic relationships for a service."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_topics WHERE service_id = ?", (service_id,))
            conn.commit()
            return cursor.rowcount

    async def delete_by_topic(self, topic: str) -> int:
        """Delete all service relationships for a topic."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM service_topics WHERE topic = ?", (topic,))
            conn.commit()
            return cursor.rowcount
