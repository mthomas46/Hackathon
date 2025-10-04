"""User Store Service - Main FastAPI Application.

This service provides persistent user storage and relationship management
for the LLM Documentation Ecosystem. It serves as the central hub for user
data, linking users to documents, services, and notification preferences.

Endpoints:
- POST /users: Create new user
- GET /users/{user_id}: Get user by ID
- PUT /users/{user_id}: Update user
- DELETE /users/{user_id}: Delete user
- GET /users: List/search users
- POST /users/{user_id}/relationships: Add document relationship
- GET /users/search: Query users by relationships
- GET /users/stats: Get user statistics
- GET /health: Service health check

Dependencies:
- Document Store (for document metadata)
- Notification Service (for user notifications)
"""

from services.shared.infrastructure.config import load_service_config

import time
import os
from contextlib import asynccontextmanager
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware

from services.shared.infrastructure.utilities import attach_self_register, setup_common_middleware

# Import domain and application layers
from .infrastructure.repositories.sqlite_user_repository import (
    SQLiteUserRepository,
    SQLiteUserPreferencesRepository
)
from .infrastructure.repositories.sqlite_document_relationship_repository import (
    SQLiteDocumentRelationshipRepository
)
from .domain.services.user_service import UserService
from .application.use_cases.create_user_use_case import CreateUserUseCase
from .application.use_cases.query_users_by_relationship_use_case import QueryUsersByRelationshipUseCase
from .application.use_cases.process_document_relationships_use_case import ProcessDocumentRelationshipsUseCase
from .application.dto.user_dto import (
    CreateUserRequest,
    UpdateUserRequest,
    UserPreferencesRequest,
    UserResponse,
    UserSearchResponse,
    UserStatsResponse
)

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

# Load service configuration
config = load_service_config("user-store")

# Extract commonly used configuration values
SERVICE_NAME = config.service_name
SERVICE_VERSION = config.service_version
DEFAULT_API_PORT = config.server.port
SERVICE_VERSION = "1.0.0"
SERVICE_TITLE = "User Store Service"

# ============================================================================
# DEPENDENCY INJECTION SETUP
# ============================================================================

# Database configuration
DATABASE_PATH = "data/user_store.db"

# Initialize repositories
user_repository = SQLiteUserRepository(DATABASE_PATH)
preferences_repository = SQLiteUserPreferencesRepository(DATABASE_PATH)
relationship_repository = SQLiteDocumentRelationshipRepository(DATABASE_PATH)

# Initialize domain services
user_service = UserService(
    user_repository=user_repository,
    preferences_repository=preferences_repository,
    relationship_repository=relationship_repository
)

# Initialize use cases
create_user_use_case = CreateUserUseCase(user_service)
query_users_use_case = QueryUsersByRelationshipUseCase(user_service)
process_document_use_case = ProcessDocumentRelationshipsUseCase(user_service)

# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    print(f"🚀 Starting {SERVICE_TITLE} v{SERVICE_VERSION}")

    # Create some sample data for development
    try:
        await create_user_use_case.execute(CreateUserRequest(
            email="admin@example.com",
            username="admin",
            display_name="System Administrator",
            role="admin"
        ))
        await create_user_use_case.execute(CreateUserRequest(
            email="analyst@example.com",
            username="analyst",
            display_name="Data Analyst",
            role="analyst"
        ))
        print("✅ Sample users created")
    except Exception as e:
        print(f"⚠️  Sample data creation failed: {e}")

    yield

    # Shutdown
    print(f"🛑 Shutting down {SERVICE_TITLE}")

# Create FastAPI app
app = FastAPI(
    title=SERVICE_TITLE,
    description=__doc__,
    version=SERVICE_VERSION,
    lifespan=lifespan
)

# Setup middleware
setup_common_middleware(app, SERVICE_NAME)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATASTORE OPERATION LOGGING
# ============================================================================
try:
    from services.shared.infrastructure.logging.datastore_operation_logger import add_datastore_logging
    
    add_datastore_logging(
        app,
        service_name="user-store",
        log_collector_url="http://localhost:8104",
        timeout_seconds=1.0
    )
except ImportError as e:
    logger.warning(f"DataStore operation logging not available: {e}")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "uptime_seconds": time.time() - getattr(app, '_start_time', time.time())
    }


@app.get("/config")
async def get_service_config():
    """Get current service configuration and sources."""
    try:
        # Get current environment variables
        env_vars = dict(os.environ)

        # Get service configuration from loaded config
        service_config = getattr(app, '_service_config', {})

        # Determine configuration sources
        config_sources = {}

        # Check for Docker environment variables
        docker_env_vars = {k: v for k, v in env_vars.items() if k.startswith(('SERVICE_', 'DB_', 'REDIS_', 'LOG_'))}

        # Check for YAML config files
        yaml_config = {}
        if hasattr(app, '_service_config') and isinstance(app._service_config, dict):
            yaml_config = app._service_config

        # Check for .env file variables
        dotenv_vars = {k: v for k, v in env_vars.items() if not k.startswith(('SERVICE_', 'DB_', 'REDIS_', 'LOG_')) and k in ['ENVIRONMENT', 'DEBUG', 'TESTING']}

        # Compile configuration sources
        if docker_env_vars:
            config_sources['docker'] = docker_env_vars
        if yaml_config:
            config_sources['yaml'] = yaml_config
        if dotenv_vars:
            config_sources['dotenv'] = dotenv_vars

        # Get runtime configuration
        runtime_config = {
            'service_name': SERVICE_NAME,
            'version': SERVICE_VERSION,
            'port': getattr(app, '_port', 'unknown'),
            'host': getattr(app, '_host', 'unknown'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'database_url': os.getenv('DB_URL', 'sqlite:///user_store.db'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        }

        return {
            'config': runtime_config,
            'sources': config_sources,
            'version': SERVICE_VERSION,
            'timestamp': time.time()
        }

    except Exception as e:
        logger.error(f"Failed to get service config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration: {e}")


@app.post(
    "/users",
    response_model=UserResponse,
    summary="Create a new user",
    description="""
    Create a new user in the system with comprehensive profile information.

    This endpoint allows creating users with:
    - Basic profile information (email, username, display name)
    - Role assignment (admin, analyst, developer, manager, viewer)
    - Topic interests for expertise tracking
    - Service subscriptions for notifications

    The system will automatically generate a unique ID and timestamps.
    """,
    responses={
        200: {"description": "User created successfully", "model": UserResponse},
        400: {"description": "Invalid user data or validation error"},
        409: {"description": "User with this email or username already exists"}
    },
    tags=["Users"]
)
async def create_user(request: CreateUserRequest):
    """Create a new user with comprehensive profile information."""
    try:
        user = await create_user_use_case.execute(
            email=request.email,
            username=request.username,
            display_name=request.display_name,
            role=request.role,
            initial_topics=request.topic_interests,
            initial_services=request.service_subscriptions
        )
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            role=user.role.value,
            status=user.status.value,
            avatar_url=user.avatar_url,
            bio=user.bio,
            document_relationships=user.document_relationships,
            service_subscriptions=user.service_subscriptions,
            topic_interests=user.topic_interests,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="""
    Retrieve a user's complete profile information by their unique identifier.

    Returns comprehensive user data including:
    - Basic profile information
    - Role and status
    - Document relationships
    - Topic interests and expertise
    - Service subscriptions
    - Activity timestamps
    """,
    responses={
        200: {"description": "User found", "model": UserResponse},
        404: {"description": "User not found"}
    },
    tags=["Users"]
)
async def get_user(user_id: str):
    """Get a user by their unique identifier."""
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        role=user.role.value,
        status=user.status.value,
        avatar_url=user.avatar_url,
        bio=user.bio,
        document_relationships=user.document_relationships,
        service_subscriptions=user.service_subscriptions,
        topic_interests=user.topic_interests,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@app.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user information",
    description="""
    Update a user's profile information. Only provided fields will be updated.

    You can update:
    - Basic profile information (display name, avatar, bio)
    - Role and status (admin only)
    - Topic interests and service subscriptions
    - Contact information and notification preferences
    """,
    responses={
        200: {"description": "User updated successfully", "model": UserResponse},
        404: {"description": "User not found"},
        400: {"description": "Invalid update data"}
    },
    tags=["Users"]
)
async def update_user(user_id: str, request: UpdateUserRequest):
    """Update a user's profile information."""
    user = await user_service.update_user(user_id, **request.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        role=user.role.value,
        status=user.status.value,
        avatar_url=user.avatar_url,
        bio=user.bio,
        document_relationships=user.document_relationships,
        service_subscriptions=user.service_subscriptions,
        topic_interests=user.topic_interests,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@app.delete(
    "/users/{user_id}",
    summary="Delete a user",
    description="""
    Permanently delete a user and all their associated data.

    This will remove:
    - User profile information
    - All document relationships
    - Topic interests and service subscriptions
    - Contact information and notification preferences

    **Warning:** This action cannot be undone.
    """,
    responses={
        200: {"description": "User deleted successfully"},
        404: {"description": "User not found"}
    },
    tags=["Users"]
)
async def delete_user(user_id: str):
    """Delete a user and all associated data."""
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}


@app.get(
    "/users/search",
    response_model=UserSearchResponse,
    summary="Search users",
    description="""
    Search for users by name, email, or username.

    The search is case-insensitive and matches partial strings.
    Results are ordered by relevance.
    """,
    responses={
        200: {"description": "Search completed", "model": UserSearchResponse}
    },
    tags=["Users"]
)
async def search_users(
    q: str = Query(..., description="Search query string"),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=100)
):
    """Search users by name, email, or username."""
    users = await user_service.search_users(q, limit)

    return UserSearchResponse(
        users=[
            UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                display_name=user.display_name,
                role=user.role.value,
                status=user.status.value,
                avatar_url=user.avatar_url,
                bio=user.bio,
                document_relationships=user.document_relationships,
                service_subscriptions=user.service_subscriptions,
                topic_interests=user.topic_interests,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ],
        total_count=len(users),
        query=q
    )


@app.get(
    "/users",
    response_model=List[UserResponse],
    summary="List users",
    description="""
    Retrieve a paginated list of users with optional filtering.

    You can filter by:
    - Role: admin, analyst, developer, manager, viewer
    - Status: active, inactive, suspended, pending

    Results are ordered by creation date (newest first).
    """,
    responses={
        200: {"description": "List of users", "model": List[UserResponse]}
    },
    tags=["Users"]
)
async def list_users(
    role: Optional[str] = Query(None, description="Filter by user role (admin, analyst, developer, manager, viewer)"),
    status: Optional[str] = Query(None, description="Filter by user status (active, inactive, suspended, pending)"),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Pagination offset", ge=0)
):
    """List users with optional filtering and pagination."""
    # Convert string to enum if provided
    user_role = None
    if role:
        from .domain.entities.user import UserRole
        user_role = getattr(UserRole, role.upper())

    user_status = None
    if status:
        from .domain.entities.user import UserStatus
        user_status = getattr(UserStatus, status.upper())

    users = await user_service.list_users(
        role=user_role,
        status=user_status,
        limit=limit,
        offset=offset
    )

    return [
        UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            role=user.role.value,
            status=user.status.value,
            avatar_url=user.avatar_url,
            bio=user.bio,
            document_relationships=user.document_relationships,
            service_subscriptions=user.service_subscriptions,
            topic_interests=user.topic_interests,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]


@app.post("/users/{user_id}/relationships")
async def add_user_document_relationship(
    user_id: str,
    document_id: str,
    relationship_type: str = "viewer",
    access_level: str = "read"
):
    """Add a relationship between a user and a document."""
    try:
        relationship = await user_service.add_user_document_relationship(
            user_id=user_id,
            document_id=document_id,
            relationship_type=relationship_type,
            access_level=access_level
        )

        return {
            "message": "Relationship created successfully",
            "relationship": {
                "id": relationship.id,
                "user_id": relationship.user_id,
                "document_id": relationship.document_id,
                "relationship_type": relationship.relationship_type.value,
                "access_level": relationship.access_level.value
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/query", response_model=List[UserResponse])
async def query_users_by_relationship(
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    service_name: Optional[str] = Query(None, description="Filter by service subscription"),
    topic: Optional[str] = Query(None, description="Filter by topic interest"),
    limit: int = Query(50, description="Maximum results")
):
    """Query users based on relationships to documents, services, and topics.

    This endpoint supports the requirements for:
    - Interpreter service queries
    - Analysis service user discovery
    - Relationship-based user filtering
    """
    users = await query_users_use_case.execute(
        document_id=document_id,
        service_name=service_name,
        topic=topic,
        limit=limit
    )

    return users


@app.get("/users/stats", response_model=UserStatsResponse)
async def get_user_stats():
    """Get comprehensive user statistics."""
    stats = await user_service.get_user_stats()
    return UserStatsResponse(**stats)


@app.put("/users/{user_id}/preferences")
async def update_user_preferences(user_id: str, request: UserPreferencesRequest):
    """Update user notification preferences."""
    preferences = await user_service.update_user_preferences(
        user_id, **request.model_dump(exclude_unset=True)
    )
    if not preferences:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": "Preferences updated successfully",
        "preferences": {
            "user_id": preferences.user_id,
            "email_notifications": preferences.email_notifications,
            "webhook_notifications": preferences.webhook_notifications,
            "notification_channels": preferences.notification_channels,
            "theme": preferences.theme,
            "timezone": preferences.timezone,
            "language": preferences.language
        }
    }


# ============================================================================
# DOCUMENT RELATIONSHIP MANAGEMENT ENDPOINTS
# ============================================================================

@app.post(
    "/users/{user_id}/documents/{document_id}",
    summary="Add document relationship",
    description="""
    Create a relationship between a user and a document.

    This establishes a connection that allows the user to access the document
    and contributes to their expertise profile based on document tags.
    """,
    responses={
        201: {"description": "Relationship created successfully"},
        400: {"description": "Invalid relationship data"},
        404: {"description": "User not found"},
        409: {"description": "Relationship already exists"}
    },
    tags=["Document Relationships"]
)
async def add_user_document_relationship(
    user_id: str,
    document_id: str,
    relationship_type: str = Query(..., description="Relationship type (owner, contributor, reviewer, subscriber, viewer)"),
    access_level: str = Query("read", description="Access level (read, write, admin)")
):
    """Add a document relationship for a user."""
    try:
        relationship = await user_service.add_user_document_relationship(
            user_id=user_id,
            document_id=document_id,
            relationship_type=relationship_type,
            access_level=access_level
        )
        return {
            "message": "Document relationship created successfully",
            "relationship": {
                "user_id": relationship.user_id,
                "document_id": relationship.document_id,
                "relationship_type": relationship.relationship_type.value,
                "access_level": relationship.access_level.value,
                "created_at": relationship.created_at.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete(
    "/users/{user_id}/documents/{document_id}",
    summary="Remove document relationship",
    description="""
    Remove the relationship between a user and a document.

    This will revoke the user's access to the document and may affect
    their expertise profile if they lose relevant document associations.
    """,
    responses={
        200: {"description": "Relationship removed successfully"},
        404: {"description": "User or relationship not found"}
    },
    tags=["Document Relationships"]
)
async def remove_user_document_relationship(user_id: str, document_id: str):
    """Remove a document relationship from a user."""
    success = await user_service.remove_user_document_relationship(user_id, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="User or relationship not found")

    return {"message": "Document relationship removed successfully"}


@app.put(
    "/users/{user_id}/documents/{document_id}",
    summary="Update document relationship",
    description="""
    Update the properties of a user's document relationship.

    You can modify the relationship type and access level.
    """,
    responses={
        200: {"description": "Relationship updated successfully"},
        404: {"description": "User or relationship not found"}
    },
    tags=["Document Relationships"]
)
async def update_user_document_relationship(
    user_id: str,
    document_id: str,
    relationship_type: Optional[str] = Query(None, description="New relationship type"),
    access_level: Optional[str] = Query(None, description="New access level")
):
    """Update a user's document relationship properties."""
    updates = {}
    if relationship_type:
        updates["relationship_type"] = relationship_type
    if access_level:
        updates["access_level"] = access_level

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    success = await user_service.update_user_document_relationship(user_id, document_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="User or relationship not found")

    return {"message": "Document relationship updated successfully"}


# ============================================================================
# TOPIC MANAGEMENT ENDPOINTS
# ============================================================================

@app.post(
    "/users/{user_id}/topics",
    summary="Add topic interest",
    description="""
    Add a topic of interest to a user's profile.

    This helps in personalizing notifications and recommendations
    based on the user's areas of interest.
    """,
    responses={
        200: {"description": "Topic added successfully"},
        400: {"description": "Topic already exists"},
        404: {"description": "User not found"}
    },
    tags=["Topics"]
)
async def add_user_topic(user_id: str, topic: str = Query(..., description="Topic name")):
    """Add a topic interest to a user."""
    try:
        user = await user_service.add_user_topic_interest(user_id, topic)
        return {
            "message": f"Topic '{topic}' added to user interests",
            "user_id": user_id,
            "topics": user.topic_interests
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete(
    "/users/{user_id}/topics/{topic}",
    summary="Remove topic interest",
    description="""
    Remove a topic from a user's interests.

    This will stop personalized recommendations and notifications
    for the removed topic.
    """,
    responses={
        200: {"description": "Topic removed successfully"},
        404: {"description": "User or topic not found"}
    },
    tags=["Topics"]
)
async def remove_user_topic(user_id: str, topic: str):
    """Remove a topic interest from a user."""
    success = await user_service.remove_user_topic_interest(user_id, topic)
    if not success:
        raise HTTPException(status_code=404, detail="User or topic not found")

    return {"message": f"Topic '{topic}' removed from user interests"}


@app.get(
    "/users/{user_id}/topics",
    summary="Get user topics",
    description="""
    Retrieve all topics of interest for a user.

    These topics are used for personalization and expertise inference.
    """,
    responses={
        200: {"description": "User topics retrieved", "model": Dict[str, List[str]]},
        404: {"description": "User not found"}
    },
    tags=["Topics"]
)
async def get_user_topics(user_id: str):
    """Get all topic interests for a user."""
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "topics": user.topic_interests,
        "expertise_tags": getattr(user, 'user_tags', [])
    }


# ============================================================================
# SERVICE SUBSCRIPTION MANAGEMENT ENDPOINTS
# ============================================================================

@app.post(
    "/users/{user_id}/services",
    summary="Subscribe to service",
    description="""
    Subscribe a user to a service for notifications and updates.

    The user will receive notifications about service-related activities
    and documents from subscribed services.
    """,
    responses={
        200: {"description": "Service subscription added"},
        400: {"description": "Already subscribed to service"},
        404: {"description": "User not found"}
    },
    tags=["Services"]
)
async def add_user_service_subscription(user_id: str, service_name: str = Query(..., description="Service name")):
    """Add a service subscription for a user."""
    try:
        user = await user_service.add_user_service_subscription(user_id, service_name)
        return {
            "message": f"Subscribed to service '{service_name}'",
            "user_id": user_id,
            "services": user.service_subscriptions
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete(
    "/users/{user_id}/services/{service_name}",
    summary="Unsubscribe from service",
    description="""
    Remove a user's subscription to a service.

    The user will no longer receive notifications about
    the unsubscribed service.
    """,
    responses={
        200: {"description": "Service subscription removed"},
        404: {"description": "User or service subscription not found"}
    },
    tags=["Services"]
)
async def remove_user_service_subscription(user_id: str, service_name: str):
    """Remove a service subscription from a user."""
    success = await user_service.remove_user_service_subscription(user_id, service_name)
    if not success:
        raise HTTPException(status_code=404, detail="User or service subscription not found")

    return {"message": f"Unsubscribed from service '{service_name}'"}


@app.get(
    "/users/{user_id}/services",
    summary="Get user service subscriptions",
    description="""
    Retrieve all service subscriptions for a user.

    These determine which services the user receives notifications from.
    """,
    responses={
        200: {"description": "Service subscriptions retrieved", "model": Dict[str, List[str]]},
        404: {"description": "User not found"}
    },
    tags=["Services"]
)
async def get_user_service_subscriptions(user_id: str):
    """Get all service subscriptions for a user."""
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "services": user.service_subscriptions
    }


@app.post("/users/{user_id}/login")
async def record_user_login(user_id: str):
    """Record a user login event."""
    user = await user_service.record_user_login(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Login recorded successfully"}


# ============================================================================
# DOCUMENT RELATIONSHIP ENDPOINTS
# ============================================================================

@app.post("/documents/{document_id}/process-relationships")
async def process_document_relationships(
    document_id: str,
    content: str = Form(..., description="Document content"),
    metadata: str = Form("{}", description="Document metadata as JSON string"),
    source_type: str = Form(..., description="Source type (github, jira, confluence)"),
    document_tags: str = Form("", description="Document tags as JSON array string"),
    auto_create_users: bool = Form(True, description="Auto-create users for unknown identifiers")
):
    """Process a document and automatically create user relationships.

    This endpoint is called by the source agent when documents are processed.
    It analyzes the document content and metadata to extract user identifiers
    and automatically creates relationships between users and documents.

    Supports markers like:
    - created by, updated by, assigned to
    - opened by, reviewed by
    - author, contributor, reporter, assignee
    """
    import json

    try:
        metadata_dict = json.loads(metadata)
        document_tags_list = json.loads(document_tags) if document_tags else None
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in metadata or document_tags")

    result = await process_document_use_case.execute(
        document_id=document_id,
        document_content=content,
        document_metadata=metadata_dict,
        source_type=source_type,
        document_tags=document_tags_list,
        auto_create_users=auto_create_users
    )

    return result


@app.get("/documents/{document_id}/users")
async def get_document_users(
    document_id: str,
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type")
):
    """Get all users related to a document.

    Returns users associated with a document through various relationship types
    like owner, contributor, reviewer, etc.
    """
    users = await process_document_use_case.get_document_users(
        document_id=document_id,
        relationship_type=relationship_type
    )

    return {"document_id": document_id, "users": users, "total": len(users)}


@app.get("/users/{user_id}/documents")
async def get_user_documents(
    user_id: str,
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type")
):
    """Get all documents related to a user.

    Returns documents associated with a user through various relationship types,
    grouped by relationship type.
    """
    documents = await process_document_use_case.get_user_documents(
        user_id=user_id,
        relationship_type=relationship_type
    )

    return {"user_id": user_id, "documents": documents}


@app.get("/relationships/stats")
async def get_relationship_stats():
    """Get relationship statistics across the system."""
    # Get user stats
    user_stats = await user_service.get_user_stats()

    # Add relationship stats
    total_relationships = 0
    # This would need to be implemented in the repositories
    relationship_stats = {
        "total_relationships": total_relationships,
        "relationship_types": ["owner", "contributor", "reviewer", "subscriber", "viewer"],
        "source_types": ["github", "jira", "confluence"]
    }

    return {
        "user_stats": user_stats,
        "relationship_stats": relationship_stats
    }


# ============================================================================
# EXPERTISE AND USER DISCOVERY ENDPOINTS
# ============================================================================

@app.get("/users/expertise/{topic}")
async def find_users_by_expertise(
    topic: str,
    min_relationships: int = Query(1, description="Minimum document relationships required")
):
    """Find users with expertise in a specific topic.

    Returns users who have demonstrated expertise in the specified topic
    based on their document relationships and tag associations.
    """
    users = await user_service.find_users_by_expertise(topic, min_relationships)

    return {
        "topic": topic,
        "min_relationships": min_relationships,
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "expertise_tags": user.user_tags,
                "relationship_count": len(user.document_relationships)
            }
            for user in users
        ],
        "total": len(users)
    }


@app.get("/users/{user_id}/expertise")
async def get_user_expertise_profile(user_id: str):
    """Get comprehensive expertise profile for a user.

    Returns detailed analysis of user's expertise areas, document types worked with,
    services experience, and expertise scores.
    """
    profile = await user_service.get_user_expertise_profile(user_id)

    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    return profile


@app.put("/users/{user_id}/contact")
async def update_user_contact_info(
    user_id: str,
    contact_email: Optional[str] = None,
    contact_webhook: Optional[str] = None,
    contact_slack: Optional[str] = None
):
    """Update user contact information for notifications.

    Allows updating alternative contact methods for notification delivery
    beyond the primary email address.
    """
    user = await user_service.update_user(
        user_id,
        contact_email=contact_email,
        contact_webhook=contact_webhook,
        contact_slack=contact_slack
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": "Contact information updated successfully",
        "user_id": user_id,
        "contacts": user.get_notification_contacts()
    }


@app.get("/users/{user_id}/contacts")
async def get_user_contacts(user_id: str):
    """Get user's notification contact information."""
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "contacts": user.get_notification_contacts(),
        "notification_preferences": user.notification_preferences
    }


# ============================================================================
# SERVICE REGISTRATION
# ============================================================================

# Register with service discovery
attach_self_register(app, SERVICE_NAME)


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("SERVICE_API_PORT", "5150"))
    host = os.getenv("SERVICE_API_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
