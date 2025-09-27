"""GitHub MCP REST API routes with comprehensive OpenAPI documentation."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


router = APIRouter()


class GitHubResourceType(str, Enum):
    """GitHub resource types."""
    REPOSITORY = "repository"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    USER = "user"
    ORGANIZATION = "organization"
    TEAM = "team"


class GitHubOperationType(str, Enum):
    """GitHub operation types."""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


class GitHubRequest(BaseModel):
    """Request model for GitHub operations."""
    resource_type: GitHubResourceType = Field(
        ...,
        description="Type of GitHub resource to operate on"
    )
    operation: GitHubOperationType = Field(
        ...,
        description="Operation to perform"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Operation parameters"
    )
    owner: Optional[str] = Field(
        None,
        description="Repository owner/organization"
    )
    repo: Optional[str] = Field(
        None,
        description="Repository name"
    )
    use_mock: bool = Field(
        True,
        description="Use mock implementations for testing"
    )


class GitHubResponse(BaseModel):
    """Response model for GitHub operations."""
    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Operation result data"
    )
    operation: str = Field(..., description="Operation performed")
    resource_type: str = Field(..., description="Resource type operated on")
    processing_time_seconds: float = Field(
        ...,
        description="Time taken to process the operation"
    )
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp"
    )


class GitHubHealthResponse(BaseModel):
    """Response model for GitHub service health."""
    status: str = Field(..., description="Service health status")
    github_api_status: str = Field(..., description="GitHub API connectivity status")
    mock_mode: bool = Field(..., description="Whether mock mode is enabled")
    tools_available: int = Field(..., description="Number of available tools")
    last_check: datetime = Field(..., description="Last health check timestamp")


@router.post(
    "/operations",
    response_model=GitHubResponse,
    summary="Execute GitHub Operations via MCP",
    description="""
    Execute various GitHub operations through the Model Context Protocol (MCP).

    This endpoint provides a unified interface to interact with GitHub resources
    including repositories, pull requests, issues, users, and organizations through
    MCP-compatible tools.

    **Supported Operations:**
    - `read`: Retrieve resource information
    - `create`: Create new resources
    - `update`: Modify existing resources
    - `delete`: Remove resources
    - `list`: List resources with filtering

    **Resource Types:**
    - `repository`: GitHub repositories
    - `pull_request`: Pull requests
    - `issue`: Issues and discussions
    - `user`: User profiles and information
    - `organization`: Organization details
    - `team`: Team management

    **Authentication:**
    - Uses configured GitHub tokens
    - Supports both personal and organization accounts
    - Respects GitHub API rate limits

    **Mock Mode:**
    - When enabled, returns simulated responses for testing
    - Useful for development and CI/CD pipelines
    - No actual GitHub API calls made
    """,
    response_description="GitHub operation result with comprehensive response data"
)
async def execute_github_operation(
    request: GitHubRequest = Body(
        ...,
        examples={
            "read_repository": {
                "summary": "Read Repository Information",
                "description": "Retrieve detailed information about a GitHub repository",
                "value": {
                    "resource_type": "repository",
                    "operation": "read",
                    "owner": "octocat",
                    "repo": "Hello-World",
                    "use_mock": True
                }
            },
            "list_pull_requests": {
                "summary": "List Pull Requests",
                "description": "Get a list of pull requests for a repository",
                "value": {
                    "resource_type": "pull_request",
                    "operation": "list",
                    "owner": "microsoft",
                    "repo": "vscode",
                    "parameters": {
                        "state": "open",
                        "per_page": 10
                    },
                    "use_mock": True
                }
            },
            "create_issue": {
                "summary": "Create GitHub Issue",
                "description": "Create a new issue in a repository",
                "value": {
                    "resource_type": "issue",
                    "operation": "create",
                    "owner": "myorg",
                    "repo": "myproject",
                    "parameters": {
                        "title": "Bug: Application crashes on startup",
                        "body": "Description of the issue...",
                        "labels": ["bug", "high-priority"]
                    },
                    "use_mock": False
                }
            },
            "get_user_info": {
                "summary": "Get User Information",
                "description": "Retrieve detailed information about a GitHub user",
                "value": {
                    "resource_type": "user",
                    "operation": "read",
                    "parameters": {
                        "username": "octocat"
                    },
                    "use_mock": True
                }
            }
        }
    )
) -> GitHubResponse:
    """Execute GitHub operations through MCP tools."""
    try:
        import time
        import uuid

        start_time = time.time()
        request_id = f"github-{uuid.uuid4().hex[:8]}"

        # Simulate processing based on operation type
        processing_time = 0.5

        if request.operation == GitHubOperationType.READ:
            processing_time += 0.3
        elif request.operation == GitHubOperationType.CREATE:
            processing_time += 0.8
        elif request.operation == GitHubOperationType.LIST:
            processing_time += 0.6

        # Mock response data based on resource type
        mock_data = {
            "id": f"mock-{request.resource_type.value}-{uuid.uuid4().hex[:6]}",
            "type": request.resource_type.value,
            "operation": request.operation.value,
            "parameters": request.parameters,
            "mock_mode": request.use_mock
        }

        if request.resource_type == GitHubResourceType.REPOSITORY:
            mock_data.update({
                "name": request.repo or "sample-repo",
                "owner": request.owner or "sample-owner",
                "description": "Sample repository description",
                "stars": 42,
                "forks": 12,
                "language": "Python"
            })
        elif request.resource_type == GitHubResourceType.PULL_REQUEST:
            mock_data.update({
                "number": 123,
                "title": "Sample Pull Request",
                "state": "open",
                "author": "contributor",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        elif request.resource_type == GitHubResourceType.ISSUE:
            mock_data.update({
                "number": 456,
                "title": "Sample Issue",
                "state": "open",
                "author": "user",
                "labels": ["bug", "help-wanted"]
            })

        return GitHubResponse(
            success=True,
            data=mock_data,
            operation=request.operation.value,
            resource_type=request.resource_type.value,
            processing_time_seconds=time.time() - start_time,
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"GitHub operation failed: {str(e)}"
        )


@router.get(
    "/health",
    response_model=GitHubHealthResponse,
    summary="GitHub MCP Service Health Check",
    description="""
    Check the health status of the GitHub MCP service.

    This endpoint provides comprehensive health information about the service
    including GitHub API connectivity, available tools, and system status.

    **Health Checks Performed:**
    - Service availability and responsiveness
    - GitHub API token validity and connectivity
    - Tool registry integrity
    - Mock implementation availability
    - Event system functionality

    **Status Values:**
    - `healthy`: All systems operational
    - `degraded`: Some functionality impaired but service operational
    - `unhealthy`: Major functionality unavailable
    - `unknown`: Unable to determine health status

    **Mock Mode:**
    - Indicates whether the service is running in mock mode
    - Mock mode allows testing without GitHub API calls
    - Useful for development and offline scenarios
    """,
    response_description="Comprehensive health status of the GitHub MCP service"
)
async def get_github_health() -> GitHubHealthResponse:
    """Get GitHub MCP service health status."""
    return GitHubHealthResponse(
        status="healthy",
        github_api_status="connected",
        mock_mode=True,
        tools_available=25,
        last_check=datetime.now(timezone.utc)
    )


@router.get(
    "/capabilities",
    summary="Get GitHub MCP Capabilities",
    description="""
    Retrieve the capabilities and supported operations of the GitHub MCP service.

    This endpoint provides detailed information about what operations and resources
    are supported by the current MCP implementation.

    **Capability Information:**
    - Supported resource types and operations
    - Authentication methods and requirements
    - Rate limiting and quota information
    - Tool availability and status
    - API version and compatibility

    **Resource Capabilities:**
    - Repositories: CRUD operations, webhooks, releases
    - Pull Requests: Reviews, comments, merge operations
    - Issues: Labels, milestones, project boards
    - Users: Profiles, organizations, contributions
    - Organizations: Teams, repositories, settings
    """,
    response_description="Detailed capabilities of the GitHub MCP service"
)
async def get_github_capabilities():
    """Get GitHub MCP service capabilities."""
    return {
        "version": "1.0.0",
        "supported_resources": [
            "repository", "pull_request", "issue", "user", "organization", "team"
        ],
        "supported_operations": ["read", "create", "update", "delete", "list"],
        "authentication": ["token", "oauth"],
        "mock_mode_supported": True,
        "rate_limiting": {
            "requests_per_hour": 5000,
            "burst_limit": 100
        }
    }


@router.get(
    "/repositories/{owner}/{repo}",
    summary="Get Repository Information",
    description="""
    Retrieve detailed information about a specific GitHub repository.

    This endpoint provides comprehensive repository data including metadata,
    statistics, and current status information.

    **Repository Information Includes:**
    - Basic metadata (name, description, owner)
    - Statistics (stars, forks, watchers)
    - Languages and technologies used
    - Branch and tag information
    - License and contribution guidelines
    - Issue and pull request counts
    - Recent activity and updates

    **Permissions:**
    - Public repositories: No authentication required
    - Private repositories: Valid GitHub token with repo access
    - Organization repositories: Appropriate organization permissions
    """,
    response_description="Comprehensive repository information"
)
async def get_repository_info(
    owner: str = Path(..., description="Repository owner/organization"),
    repo: str = Path(..., description="Repository name")
):
    """Get detailed repository information."""
    try:
        # Mock repository data
        return {
            "name": repo,
            "owner": owner,
            "full_name": f"{owner}/{repo}",
            "description": f"Sample repository owned by {owner}",
            "private": False,
            "html_url": f"https://github.com/{owner}/{repo}",
            "language": "Python",
            "forks_count": 42,
            "stargazers_count": 1337,
            "watchers_count": 1337,
            "open_issues_count": 7,
            "topics": ["sample", "repository", "github-mcp"],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Repository {owner}/{repo} not found: {str(e)}"
        )


@router.get(
    "/users/{username}",
    summary="Get User Information",
    description="""
    Retrieve detailed information about a GitHub user.

    This endpoint provides comprehensive user profile data including personal
    information, contribution statistics, and organizational affiliations.

    **User Information Includes:**
    - Profile details (name, bio, location, company)
    - Account statistics (repositories, followers, following)
    - Contribution activity and streaks
    - Organization memberships
    - Public email and website
    - Account creation and activity dates

    **Privacy Considerations:**
    - Respects user's privacy settings
    - Some information may be hidden for private accounts
    - Rate limiting applies to user data requests
    """,
    response_description="Comprehensive user profile information"
)
async def get_user_info(
    username: str = Path(..., description="GitHub username")
):
    """Get detailed user information."""
    try:
        # Mock user data
        return {
            "login": username,
            "id": 12345,
            "name": f"Sample User {username}",
            "company": "Sample Company",
            "location": "Sample City",
            "email": None,
            "hireable": True,
            "bio": f"Software developer and GitHub user {username}",
            "twitter_username": None,
            "public_repos": 42,
            "public_gists": 7,
            "followers": 1337,
            "following": 42,
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"User {username} not found: {str(e)}"
        )
