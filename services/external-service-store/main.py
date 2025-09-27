"""External Service Store - FastAPI Application.

A lightweight service for managing external service metadata, relationships,
and technical specifications in the LLM Documentation Ecosystem.
"""

import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .infrastructure.repositories.sqlite_external_service_repository import (
    SQLiteExternalServiceRepository,
    SQLiteServiceEndpointRepository,
    SQLiteServiceDependencyRepository,
    SQLiteServiceDocumentRepository,
    SQLiteServiceUserRepository,
    SQLiteServiceTopicRepository
)
from .domain.services.external_service_service import ExternalServiceService

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

SERVICE_NAME = "external-service-store"
SERVICE_VERSION = "1.0.0"
SERVICE_TITLE = "External Service Store"
SERVICE_DESCRIPTION = """
A lightweight SQLite-based service for managing external service metadata,
relationships, and technical specifications in the LLM Documentation Ecosystem.

Features:
- Service metadata management (versions, technologies, dependencies)
- API endpoint documentation with data contracts
- Document and user relationship tracking
- Topic-based service discovery
- Comprehensive search and filtering capabilities
"""

# ============================================================================
# DEPENDENCY INJECTION SETUP
# ============================================================================

# Database configuration
DATABASE_PATH = "data/external_service_store.db"

# Initialize repositories
service_repo = SQLiteExternalServiceRepository(DATABASE_PATH)
endpoint_repo = SQLiteServiceEndpointRepository(DATABASE_PATH)
dependency_repo = SQLiteServiceDependencyRepository(DATABASE_PATH)
document_repo = SQLiteServiceDocumentRepository(DATABASE_PATH)
user_repo = SQLiteServiceUserRepository(DATABASE_PATH)
topic_repo = SQLiteServiceTopicRepository(DATABASE_PATH)

# Initialize domain service
external_service_service = ExternalServiceService(
    service_repo=service_repo,
    endpoint_repo=endpoint_repo,
    dependency_repo=dependency_repo,
    document_repo=document_repo,
    user_repo=user_repo,
    topic_repo=topic_repo
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ServiceEndpointModel(BaseModel):
    """API endpoint model."""
    path: str = Field(..., description="API endpoint path")
    method: str = Field("GET", description="HTTP method")
    description: str = Field("", description="Endpoint description")
    request_contract: Dict[str, Any] = Field(default_factory=dict, description="Request data contract")
    response_contract: Dict[str, Any] = Field(default_factory=dict, description="Response data contract")
    response_types: List[str] = Field(default_factory=list, description="Possible response content types")
    parameters: List[Dict[str, Any]] = Field(default_factory=list, description="Query/path parameters")
    authentication_required: bool = Field(False, description="Whether authentication is required")
    rate_limit: Optional[str] = Field(None, description="Rate limiting information")


class ServiceDependencyModel(BaseModel):
    """Service dependency model."""
    dependent_service_id: str = Field(..., description="ID of the service that has the dependency")
    dependency_service_id: str = Field(..., description="ID of the service being depended upon")
    dependency_type: str = Field("runtime", description="Type of dependency (runtime, build, optional)")
    version_constraint: Optional[str] = Field(None, description="Version constraint for the dependency")
    description: str = Field("", description="Description of the dependency")
    is_required: bool = Field(True, description="Whether the dependency is required")


class ServiceDocumentModel(BaseModel):
    """Service document relationship model."""
    document_id: str = Field(..., description="Document identifier")
    document_type: str = Field(..., description="Type of document (confluence, jira, github_pr, etc.)")
    relationship_type: str = Field("reference", description="How the service relates to the document")
    description: str = Field("", description="Description of the relationship")
    tags: List[str] = Field(default_factory=list, description="Tags associated with this relationship")


class ServiceUserModel(BaseModel):
    """Service user relationship model."""
    user_id: str = Field(..., description="User identifier")
    relationship_type: str = Field("maintainer", description="Type of relationship (maintainer, contributor, user)")
    role: Optional[str] = Field(None, description="Specific role in the service")
    permissions: List[str] = Field(default_factory=list, description="User permissions for the service")


class ServiceTopicModel(BaseModel):
    """Service topic relationship model."""
    topic: str = Field(..., description="Topic name")
    relevance_score: int = Field(50, description="How relevant this topic is (0-100)", ge=0, le=100)
    description: str = Field("", description="Description of topic relevance")
    tags: List[str] = Field(default_factory=list, description="Additional tags for this topic relationship")


class CreateServiceRequest(BaseModel):
    """Request model for creating a service."""
    name: str = Field(..., description="Unique service name (kebab-case)")
    display_name: Optional[str] = Field(None, description="Human-readable display name")
    description: str = Field("", description="Service description")
    service_type: str = Field("api", description="Service type (api, database, message_queue, etc.)")
    version: str = Field("1.0.0", description="Current version (semantic versioning)")
    technologies: List[str] = Field(default_factory=list, description="Technologies used by the service")
    run_requirements: Dict[str, Any] = Field(default_factory=dict, description="Runtime requirements")
    base_url: Optional[str] = Field(None, description="Base URL for the service")
    port: Optional[int] = Field(None, description="Service port number")
    health_endpoint: Optional[str] = Field(None, description="Health check endpoint path")


class UpdateServiceRequest(BaseModel):
    """Request model for updating a service."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    service_type: Optional[str] = None
    status: Optional[str] = None
    version: Optional[str] = None
    technologies: Optional[List[str]] = None
    run_requirements: Optional[Dict[str, Any]] = None
    base_url: Optional[str] = None
    port: Optional[int] = None
    health_endpoint: Optional[str] = None
    owner: Optional[str] = None
    maintainers: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class ServiceResponse(BaseModel):
    """Response model for service data."""
    id: str
    name: str
    display_name: str
    description: str
    summary: str
    service_type: str
    status: str
    version: str
    latest_release: Optional[str]
    release_date: Optional[str]
    technologies: List[str]
    run_requirements: Dict[str, Any]
    base_url: Optional[str]
    port: Optional[int]
    health_endpoint: Optional[str]
    endpoints: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]
    documents: List[Dict[str, Any]]
    users: List[Dict[str, Any]]
    topics: List[Dict[str, Any]]
    last_confluence_document: Optional[str]
    last_jira_ticket: Optional[str]
    last_github_pr: Optional[str]
    data_contracts: Dict[str, Any]
    owner: Optional[str]
    maintainers: List[str]
    tags: List[str]
    created_at: str
    updated_at: str


class ServiceSearchResponse(BaseModel):
    """Response model for service search results."""
    services: List[ServiceResponse]
    total_count: int
    query: str


# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title=SERVICE_TITLE,
    description=SERVICE_DESCRIPTION,
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store start time for uptime calculation
app._start_time = time.time()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "uptime_seconds": time.time() - getattr(app, '_start_time', time.time()),
        "database": "sqlite"
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "External Service Metadata Store",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "services": "/services"
        }
    }


# ============================================================================
# SERVICE CRUD ENDPOINTS
# ============================================================================

@app.post(
    "/services",
    response_model=ServiceResponse,
    summary="Create a new external service",
    description="""
    Register a new external service in the ecosystem with comprehensive metadata.

    This endpoint creates a service entry with:
    - Basic service information (name, type, version)
    - Technical specifications (technologies, requirements)
    - Operational details (URLs, ports, health checks)
    """,
    responses={
        200: {"description": "Service created successfully", "model": ServiceResponse},
        400: {"description": "Invalid service data"},
        409: {"description": "Service with this name already exists"}
    },
    tags=["Services"]
)
async def create_service(request: CreateServiceRequest):
    """Create a new external service."""
    try:
        service = await external_service_service.create_service(
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            service_type=request.service_type,
            version=request.version
        )

        # Update additional fields
        if request.technologies:
            service.technologies = request.technologies
        if request.run_requirements:
            service.run_requirements = request.run_requirements
        if request.base_url:
            service.base_url = request.base_url
        if request.port:
            service.port = request.port
        if request.health_endpoint:
            service.health_endpoint = request.health_endpoint

        await service_repo.update(service)

        # Load full service data for response
        full_service = await external_service_service.get_service(service.id)
        return ServiceResponse(**full_service.__dict__) if full_service else None

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/services/{service_id}",
    response_model=ServiceResponse,
    summary="Get service by ID",
    description="""
    Retrieve complete information about an external service including:
    - Service metadata and specifications
    - API endpoints with data contracts
    - Dependencies and relationships
    - Associated documents, users, and topics
    - Recent activity and version information
    """,
    responses={
        200: {"description": "Service found", "model": ServiceResponse},
        404: {"description": "Service not found"}
    },
    tags=["Services"]
)
async def get_service(service_id: str):
    """Get a service by its unique identifier."""
    service = await external_service_service.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    return ServiceResponse(**service.__dict__)


@app.put(
    "/services/{service_id}",
    response_model=ServiceResponse,
    summary="Update service information",
    description="""
    Update an external service's metadata and specifications.

    You can update:
    - Basic information (description, version, status)
    - Technical specifications (technologies, requirements)
    - Operational details (URLs, ports)
    - Ownership and maintenance information
    """,
    responses={
        200: {"description": "Service updated successfully", "model": ServiceResponse},
        404: {"description": "Service not found"}
    },
    tags=["Services"]
)
async def update_service(service_id: str, request: UpdateServiceRequest):
    """Update a service's information."""
    try:
        service = await external_service_service.update_service(service_id, **request.model_dump(exclude_unset=True))
        return ServiceResponse(**service.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete(
    "/services/{service_id}",
    summary="Delete a service",
    description="""
    Permanently delete an external service and all its associated data.

    This will remove:
    - Service metadata and specifications
    - All API endpoints and data contracts
    - Dependencies and relationships
    - Document, user, and topic associations

    **Warning:** This action cannot be undone.
    """,
    responses={
        200: {"description": "Service deleted successfully"},
        404: {"description": "Service not found"}
    },
    tags=["Services"]
)
async def delete_service(service_id: str):
    """Delete a service and all associated data."""
    success = await external_service_service.delete_service(service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")

    return {"message": "Service deleted successfully"}


@app.get(
    "/services",
    response_model=List[ServiceResponse],
    summary="List services",
    description="""
    Retrieve a paginated list of external services with optional filtering.

    You can filter by:
    - Service type (api, database, message_queue, etc.)
    - Status (active, inactive, deprecated, maintenance)
    - Pagination with limit and offset
    """,
    responses={
        200: {"description": "List of services", "model": List[ServiceResponse]}
    },
    tags=["Services"]
)
async def list_services(
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    status: Optional[str] = Query(None, description="Filter by service status"),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Pagination offset", ge=0)
):
    """List services with optional filtering."""
    services = await external_service_service.list_services(
        service_type=service_type,
        status=status,
        limit=limit,
        offset=offset
    )

    return [ServiceResponse(**service.__dict__) for service in services]


@app.get(
    "/services/search",
    response_model=ServiceSearchResponse,
    summary="Search services",
    description="""
    Search for external services by name, description, or tags.

    The search is case-insensitive and matches partial strings across:
    - Service names and display names
    - Descriptions and summaries
    - Technology stacks and tags
    """,
    responses={
        200: {"description": "Search completed", "model": ServiceSearchResponse}
    },
    tags=["Services"]
)
async def search_services(
    q: str = Query(..., description="Search query string"),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=100)
):
    """Search services by name, description, or tags."""
    services = await external_service_service.search_services(q, limit)

    return ServiceSearchResponse(
        services=[ServiceResponse(**service.__dict__) for service in services],
        total_count=len(services),
        query=q
    )


# ============================================================================
# ENDPOINT MANAGEMENT ENDPOINTS
# ============================================================================

@app.post(
    "/services/{service_id}/endpoints",
    summary="Add API endpoint",
    description="""
    Add an API endpoint to a service with comprehensive data contracts.

    Each endpoint can include:
    - HTTP method and path
    - Request/response data contracts
    - Authentication and rate limiting requirements
    - Parameter specifications
    """,
    responses={
        200: {"description": "Endpoint added successfully"},
        400: {"description": "Invalid endpoint data"},
        404: {"description": "Service not found"},
        409: {"description": "Endpoint already exists"}
    },
    tags=["Endpoints"]
)
async def add_service_endpoint(service_id: str, endpoint: ServiceEndpointModel):
    """Add an API endpoint to a service."""
    try:
        result = await external_service_service.add_service_endpoint(
            service_id=service_id,
            path=endpoint.path,
            method=endpoint.method,
            description=endpoint.description,
            request_contract=endpoint.request_contract,
            response_contract=endpoint.response_contract,
            response_types=endpoint.response_types
        )
        return {
            "message": "Endpoint added successfully",
            "endpoint": {
                "id": result.id,
                "path": result.path,
                "method": result.method,
                "description": result.description
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/services/{service_id}/endpoints",
    summary="Get service endpoints",
    description="""
    Retrieve all API endpoints for a service with their data contracts.

    Returns complete endpoint specifications including:
    - HTTP methods and paths
    - Request/response contracts
    - Authentication requirements
    - Rate limiting information
    """,
    responses={
        200: {"description": "Service endpoints retrieved"},
        404: {"description": "Service not found"}
    },
    tags=["Endpoints"]
)
async def get_service_endpoints(service_id: str):
    """Get all endpoints for a service."""
    endpoints = await external_service_service.get_service(service_id)
    if not endpoints:
        raise HTTPException(status_code=404, detail="Service not found")

    return {"service_id": service_id, "endpoints": [ep.__dict__ for ep in endpoints.endpoints]}


# ============================================================================
# DEPENDENCY MANAGEMENT ENDPOINTS
# ============================================================================

@app.post(
    "/services/dependencies",
    summary="Add service dependency",
    description="""
    Create a dependency relationship between two services.

    Dependencies can be:
    - Runtime dependencies (required for operation)
    - Build dependencies (required for development)
    - Optional dependencies (enhancement features)
    """,
    responses={
        200: {"description": "Dependency added successfully"},
        400: {"description": "Invalid dependency data"},
        404: {"description": "One or both services not found"}
    },
    tags=["Dependencies"]
)
async def add_service_dependency(dependency: ServiceDependencyModel):
    """Add a dependency between services."""
    try:
        result = await external_service_service.add_service_dependency(
            dependent_service_id=dependency.dependent_service_id,
            dependency_service_id=dependency.dependency_service_id,
            dependency_type=dependency.dependency_type,
            version_constraint=dependency.version_constraint,
            description=dependency.description,
            is_required=dependency.is_required
        )
        return {
            "message": "Dependency added successfully",
            "dependency": {
                "id": result.id,
                "dependent": result.dependent_service_id,
                "dependency": result.dependency_service_id,
                "type": result.dependency_type
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/services/{service_id}/dependencies",
    summary="Get service dependencies",
    description="""
    Retrieve all services that the specified service depends on.

    Includes dependency types, version constraints, and descriptions.
    """,
    responses={
        200: {"description": "Service dependencies retrieved"},
        404: {"description": "Service not found"}
    },
    tags=["Dependencies"]
)
async def get_service_dependencies(service_id: str):
    """Get all dependencies for a service."""
    dependencies = await external_service_service.get_service_dependencies(service_id)
    return {"service_id": service_id, "dependencies": [dep.__dict__ for dep in dependencies]}


@app.get(
    "/services/{service_id}/dependents",
    summary="Get services that depend on this service",
    description="""
    Retrieve all services that depend on the specified service.

    Shows the reverse dependency relationships.
    """,
    responses={
        200: {"description": "Service dependents retrieved"},
        404: {"description": "Service not found"}
    },
    tags=["Dependencies"]
)
async def get_service_dependents(service_id: str):
    """Get all services that depend on the given service."""
    dependents = await external_service_service.get_service_dependents(service_id)
    return {"service_id": service_id, "dependents": [dep.__dict__ for dep in dependents]}


# ============================================================================
# DOCUMENT RELATIONSHIP ENDPOINTS
# ============================================================================

@app.post(
    "/services/{service_id}/documents",
    summary="Add document relationship",
    description="""
    Associate a document with a service and specify the relationship type.

    Documents can be related as:
    - References (general documentation)
    - Implementations (code/docs that implement the service)
    - Documentation (service-specific docs)
    """,
    responses={
        200: {"description": "Document relationship added"},
        400: {"description": "Invalid relationship data"},
        404: {"description": "Service not found"}
    },
    tags=["Documents"]
)
async def add_service_document(service_id: str, document: ServiceDocumentModel):
    """Add a document relationship to a service."""
    try:
        result = await external_service_service.add_service_document(
            service_id=service_id,
            document_id=document.document_id,
            document_type=document.document_type,
            relationship_type=document.relationship_type,
            description=document.description,
            tags=document.tags
        )
        return {
            "message": "Document relationship added successfully",
            "relationship": {
                "id": result.id,
                "service_id": result.service_id,
                "document_id": result.document_id,
                "document_type": result.document_type,
                "relationship_type": result.relationship_type
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/services/{service_id}/documents",
    summary="Get service documents",
    description="""
    Retrieve all documents associated with a service.

    Optionally filter by document type (confluence, jira, github_pr, etc.).
    """,
    responses={
        200: {"description": "Service documents retrieved"},
        404: {"description": "Service not found"}
    },
    tags=["Documents"]
)
async def get_service_documents(service_id: str, document_type: Optional[str] = None):
    """Get all documents related to a service."""
    documents = await external_service_service.get_service_documents(service_id, document_type)
    return {"service_id": service_id, "documents": [doc.__dict__ for doc in documents]}


@app.get(
    "/documents/{document_id}/services",
    summary="Get services by document",
    description="""
    Find all services that are related to a specific document.

    Shows which services reference or are documented by the given document.
    """,
    responses={
        200: {"description": "Services for document retrieved"}
    },
    tags=["Documents"]
)
async def get_services_by_document(document_id: str):
    """Get all services related to a document."""
    relationships = await document_repo.find_by_document(document_id)
    return {"document_id": document_id, "services": [rel.__dict__ for rel in relationships]}


# ============================================================================
# USER RELATIONSHIP ENDPOINTS
# ============================================================================

@app.post(
    "/services/{service_id}/users",
    summary="Add user relationship",
    description="""
    Associate a user with a service and define their relationship type.

    Users can be related as:
    - Maintainers (responsible for the service)
    - Contributors (contribute to the service)
    - Users (use the service)
    """,
    responses={
        200: {"description": "User relationship added"},
        400: {"description": "Invalid relationship data"},
        404: {"description": "Service not found"},
        409: {"description": "User relationship already exists"}
    },
    tags=["Users"]
)
async def add_service_user(service_id: str, user: ServiceUserModel):
    """Add a user relationship to a service."""
    try:
        result = await external_service_service.add_service_user(
            service_id=service_id,
            user_id=user.user_id,
            relationship_type=user.relationship_type,
            role=user.role,
            permissions=user.permissions
        )
        return {
            "message": "User relationship added successfully",
            "relationship": {
                "id": result.id,
                "service_id": result.service_id,
                "user_id": result.user_id,
                "relationship_type": result.relationship_type,
                "role": result.role
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/services/{service_id}/users",
    summary="Get service users",
    description="""
    Retrieve all users associated with a service.

    Optionally filter by relationship type (maintainer, contributor, user).
    """,
    responses={
        200: {"description": "Service users retrieved"},
        404: {"description": "Service not found"}
    },
    tags=["Users"]
)
async def get_service_users(service_id: str, relationship_type: Optional[str] = None):
    """Get all users related to a service."""
    users = await external_service_service.get_service_users(service_id, relationship_type)
    return {"service_id": service_id, "users": [user.__dict__ for user in users]}


@app.get(
    "/users/{user_id}/services",
    summary="Get user services",
    description="""
    Retrieve all services that a user is associated with.

    Shows the services the user maintains, contributes to, or uses.
    """,
    responses={
        200: {"description": "User services retrieved"}
    },
    tags=["Users"]
)
async def get_user_services(user_id: str):
    """Get all services related to a user."""
    relationships = await user_repo.find_by_user(user_id)
        return {"user_id": user_id, "services": [rel.__dict__ for rel in relationships]}


# ============================================================================
# DOCUMENT-SERVICE BIDIRECTIONAL RELATIONSHIPS
# ============================================================================

@app.post(
    "/documents/{document_id}/process-relationships",
    summary="Process document and create service relationships",
    description="""
    Analyze a document's content and automatically create bidirectional relationships
    with services mentioned within it. This establishes two-way links between
    documents and services for enhanced discoverability and relationship tracking.

    The system will:
    1. Scan document content for service mentions
    2. Detect services by name, display name, and other identifiers
    3. Create relationships in both directions (document ↔ service)
    4. Update service activity tracking for recent documents
    """,
    responses={
        200: {"description": "Document processed and relationships created"},
        400: {"description": "Invalid document data"}
    },
    tags=["Document Relationships"]
)
async def process_document_relationships(
    document_id: str,
    content: str = Form(..., description="Document content to analyze"),
    metadata: str = Form("{}", description="Document metadata as JSON string"),
    document_type: str = Form("unknown", description="Type of document (confluence, jira, github_pr, etc.)")
):
    """Process a document and automatically create relationships with detected services."""
    import json

    try:
        metadata_dict = json.loads(metadata) if metadata else None
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON")

    result = await external_service_service.create_document_service_relationships(
        document_id=document_id,
        document_content=content,
        document_metadata=metadata_dict,
        document_type=document_type
    )

    return result


@app.post(
    "/documents/{document_id}/sync-relationships",
    summary="Synchronize document-service relationships",
    description="""
    Bulk synchronize relationships between a document and multiple services.
    Useful for establishing relationships from external sources or bulk operations.

    This creates bidirectional relationships and can be used to:
    - Import relationships from external systems
    - Bulk update document associations
    - Synchronize with document store changes
    """,
    responses={
        200: {"description": "Relationships synchronized successfully"},
        400: {"description": "Invalid synchronization data"}
    },
    tags=["Document Relationships"]
)
async def sync_document_relationships(
    document_id: str,
    service_ids: str = Form(..., description="Comma-separated list of service IDs"),
    document_type: str = Form("unknown", description="Type of document"),
    relationship_type: str = Form("reference", description="Type of relationship")
):
    """Synchronize relationships between a document and multiple services."""
    service_ids_list = [sid.strip() for sid in service_ids.split(",") if sid.strip()]

    if not service_ids_list:
        raise HTTPException(status_code=400, detail="No service IDs provided")

    result = await external_service_service.sync_document_relationships(
        document_id=document_id,
        service_ids=service_ids_list,
        document_type=document_type,
        relationship_type=relationship_type
    )

    return result


@app.get(
    "/documents/{document_id}/services",
    summary="Get services related to a document",
    description="""
    Retrieve all services that are related to a specific document.
    Shows bidirectional relationships where services are referenced in documents.

    This helps understand:
    - Which services are documented in a particular document
    - Service dependencies mentioned in documentation
    - Cross-references between documentation and services
    """,
    responses={
        200: {"description": "Services related to document retrieved"},
        404: {"description": "Document not found"}
    },
    tags=["Document Relationships"]
)
async def get_document_services(document_id: str):
    """Get all services related to a specific document."""
    services = await external_service_service.get_document_services(document_id)

    return {
        "document_id": document_id,
        "services": [
            {
                "id": service.id,
                "name": service.name,
                "display_name": service.display_name,
                "description": service.description,
                "service_type": service.service_type.value,
                "status": service.status.value,
                "version": service.version
            }
            for service in services
        ],
        "total": len(services)
    }


@app.get(
    "/services/{service_id}/documents-paginated",
    summary="Get paginated documents for a service",
    description="""
    Retrieve documents related to a service with pagination support.
    Allows filtering by document type and provides detailed relationship information.

    Useful for:
    - Browsing all documentation for a service
    - Finding specific types of documents (API docs, READMEs, etc.)
    - Managing large numbers of document relationships
    """,
    responses={
        200: {"description": "Paginated documents for service retrieved"},
        404: {"description": "Service not found"}
    },
    tags=["Document Relationships"]
)
async def get_service_documents_paginated(
    service_id: str,
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Pagination offset", ge=0)
):
    """Get paginated list of documents for a service."""
    result = await external_service_service.get_service_documents_paginated(
        service_id=service_id,
        document_type=document_type,
        limit=limit,
        offset=offset
    )

    return result


@app.get(
    "/relationships/health",
    summary="Relationship health check",
    description="""
    Perform a comprehensive health check on service-document relationships.
    Provides statistics about relationship consistency, orphaned relationships,
    and overall system health.

    Useful for:
    - Monitoring relationship data quality
    - Identifying orphaned or broken relationships
    - System health monitoring and alerting
    """,
    responses={
        200: {"description": "Relationship health check completed"}
    },
    tags=["Analytics"]
)
async def get_relationship_health_check():
    """Get comprehensive health check for service-document relationships."""
    health_check = await external_service_service.get_relationship_health_check()
    return health_check


@app.get(
    "/relationships/cross-reference",
    summary="Cross-reference services and documents",
    description="""
    Get a comprehensive view of relationships between services and documents.
    Shows bidirectional mappings and helps understand the ecosystem's
    documentation and service landscape.

    Returns aggregated statistics and relationship mappings for:
    - Services with their document counts
    - Documents with their service references
    - Overall relationship health metrics
    """,
    responses={
        200: {"description": "Cross-reference analysis completed"}
    },
    tags=["Analytics"]
)
async def get_relationships_cross_reference():
    """Get cross-reference analysis of service-document relationships."""
    # Get all services and their document relationships
    services = await service_repo.list_all_services(limit=1000)
    documents = await document_repo.list_all_documents(limit=10000)

    # Build cross-reference mappings
    service_document_counts = {}
    document_service_counts = {}
    relationship_types = {}

    for service in services:
        full_service = await external_service_service.get_service(service.id)
        if full_service:
            service_document_counts[service.id] = {
                'service_name': service.name,
                'document_count': len(full_service.documents),
                'document_types': {}
            }
            for doc in full_service.documents:
                doc_type = doc.document_type
                if doc_type not in service_document_counts[service.id]['document_types']:
                    service_document_counts[service.id]['document_types'][doc_type] = 0
                service_document_counts[service.id]['document_types'][doc_type] += 1

    for doc in documents:
        if doc.document_id not in document_service_counts:
            document_service_counts[doc.document_id] = {
                'document_type': doc.document_type,
                'service_count': 0,
                'services': []
            }
        document_service_counts[doc.document_id]['service_count'] += 1
        document_service_counts[doc.document_id]['services'].append(doc.service_id)

        # Track relationship types
        rel_type = doc.relationship_type
        if rel_type not in relationship_types:
            relationship_types[rel_type] = 0
        relationship_types[rel_type] += 1

    return {
        'summary': {
            'total_services': len(services),
            'total_documents': len(documents),
            'total_relationships': len(documents),
            'relationship_types': relationship_types
        },
        'services_by_document_count': sorted(
            [
                {**data, 'service_id': service_id}
                for service_id, data in service_document_counts.items()
            ],
            key=lambda x: x['document_count'],
            reverse=True
        )[:20],  # Top 20 services by document count
        'documents_by_service_count': sorted(
            [
                {**data, 'document_id': doc_id}
                for doc_id, data in document_service_counts.items()
            ],
            key=lambda x: x['service_count'],
            reverse=True
        )[:20]  # Top 20 documents by service count
    }


# ============================================================================
# TOPIC RELATIONSHIP ENDPOINTS
# ============================================================================

@app.post(
    "/services/{service_id}/topics",
    summary="Add topic relationship",
    description="""
    Associate a topic with a service and specify relevance.

    Topics help categorize services and enable discovery based on:
    - Technical domains (machine-learning, api-design, etc.)
    - Business domains (finance, healthcare, etc.)
    - Operational concerns (monitoring, security, etc.)
    """,
    responses={
        200: {"description": "Topic relationship added"},
        400: {"description": "Invalid topic data"},
        404: {"description": "Service not found"},
        409: {"description": "Topic relationship already exists"}
    },
    tags=["Topics"]
)
async def add_service_topic(service_id: str, topic: ServiceTopicModel):
    """Add a topic relationship to a service."""
    try:
        result = await external_service_service.add_service_topic(
            service_id=service_id,
            topic=topic.topic,
            relevance_score=topic.relevance_score,
            description=topic.description,
            tags=topic.tags
        )
        return {
            "message": "Topic relationship added successfully",
            "relationship": {
                "id": result.id,
                "service_id": result.service_id,
                "topic": result.topic,
                "relevance_score": result.relevance_score
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/services/{service_id}/topics",
    summary="Get service topics",
    description="""
    Retrieve all topics associated with a service.

    Topics are ranked by relevance score to show the most
    important domains for each service.
    """,
    responses={
        200: {"description": "Service topics retrieved"},
        404: {"description": "Service not found"}
    },
    tags=["Topics"]
)
async def get_service_topics(service_id: str):
    """Get all topics related to a service."""
    topics = await external_service_service.get_service_topics(service_id)
    return {"service_id": service_id, "topics": [topic.__dict__ for topic in topics]}


@app.get(
    "/topics/{topic}/services",
    summary="Get services by topic",
    description="""
    Find all services related to a specific topic.

    Useful for discovering services in specific technical or business domains.
    """,
    responses={
        200: {"description": "Services for topic retrieved"}
    },
    tags=["Topics"]
)
async def get_services_by_topic(topic: str):
    """Get all services related to a topic."""
    relationships = await topic_repo.find_by_topic(topic)
    return {"topic": topic, "services": [rel.__dict__ for rel in relationships]}


# ============================================================================
# ANALYTICS AND DISCOVERY ENDPOINTS
# ============================================================================

@app.get(
    "/analytics/overview",
    summary="Get service ecosystem overview",
    description="""
    Retrieve analytics about the entire service ecosystem including:
    - Total number of services by type and status
    - Health metrics and distribution
    - Most active services and recent updates
    """,
    responses={
        200: {"description": "Ecosystem analytics retrieved"}
    },
    tags=["Analytics"]
)
async def get_ecosystem_overview():
    """Get comprehensive overview of the service ecosystem."""
    overview = await external_service_service.get_service_health_overview()

    # Add additional analytics
    total_endpoints = 0
    total_dependencies = 0
    total_documents = 0
    total_users = 0
    total_topics = 0

    services = await service_repo.list_all_services(limit=1000)
    for service in services:
        full_service = await external_service_service.get_service(service.id)
        if full_service:
            total_endpoints += len(full_service.endpoints)
            total_dependencies += len(full_service.dependencies)
            total_documents += len(full_service.documents)
            total_users += len(full_service.users)
            total_topics += len(full_service.topics)

    overview.update({
        "relationships": {
            "total_endpoints": total_endpoints,
            "total_dependencies": total_dependencies,
            "total_documents": total_documents,
            "total_users": total_users,
            "total_topics": total_topics
        }
    })

    return overview


@app.get(
    "/services/by-technology/{technology}",
    summary="Find services by technology",
    description="""
    Discover all services that use a specific technology.

    Useful for finding services that use particular programming languages,
    frameworks, databases, or other technical components.
    """,
    responses={
        200: {"description": "Services using technology retrieved"}
    },
    tags=["Discovery"]
)
async def get_services_by_technology(technology: str):
    """Find all services using a specific technology."""
    services = await service_repo.find_services_by_technology(technology)
    return {
        "technology": technology,
        "services": [ServiceResponse(**service.__dict__) for service in services],
        "total": len(services)
    }


@app.get(
    "/services/by-user/{user_id}",
    summary="Find services by user",
    description="""
    Discover all services that a specific user is associated with.

    Shows services the user maintains, contributes to, or uses.
    """,
    responses={
        200: {"description": "Services for user retrieved"}
    },
    tags=["Discovery"]
)
async def get_services_by_user(user_id: str):
    """Find all services related to a user."""
    services = await service_repo.find_services_by_user(user_id)
    return {
        "user_id": user_id,
        "services": [ServiceResponse(**service.__dict__) for service in services],
        "total": len(services)
    }


@app.get(
    "/services/recent-activity/{service_id}",
    summary="Get recent service activity",
    description="""
    Retrieve recent activity summary for a service including:
    - Latest document updates (Confluence, Jira, GitHub PR)
    - Recent user interactions
    - Version changes and releases
    """,
    responses={
        200: {"description": "Recent activity retrieved"},
        404: {"description": "Service not found"}
    },
    tags=["Activity"]
)
async def get_recent_service_activity(service_id: str):
    """Get recent activity summary for a service."""
    activity = await external_service_service.get_recent_service_activity(service_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Service not found")

    return activity


# ============================================================================
# SERVICE REGISTRATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
