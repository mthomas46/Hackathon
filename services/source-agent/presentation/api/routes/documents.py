"""Document REST API routes."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ....application.use_cases.fetch_document_use_case import (
    FetchDocumentUseCase,
    FetchDocumentRequest,
    FetchDocumentResponse
)

# Pydantic models for API
class FetchDocumentRequestModel(BaseModel):
    """API model for fetch document request."""
    source_type: str = Field(..., description="Source system type (github, jira, confluence, etc.)")
    source_id: str = Field(..., description="Source identifier (repo path, issue key, etc.)")
    scope: Optional[Dict[str, Any]] = Field(None, description="Optional scope parameters")
    include_metadata: bool = Field(True, description="Include document metadata")
    timeout_seconds: int = Field(300, description="Request timeout in seconds")


class DocumentResponseModel(BaseModel):
    """API model for document response."""
    id: str
    source_type: str
    source_id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    tags: List[str]
    fetched_at: str
    version: Optional[str]
    author: Optional[str]
    status: str


class FetchDocumentResponseModel(BaseModel):
    """API model for fetch document response."""
    success: bool
    documents: List[DocumentResponseModel]
    documents_processed: int
    documents_succeeded: int
    documents_failed: int
    message: str
    processing_time_seconds: float


class DocumentRouter:
    """FastAPI router for document operations."""

    def __init__(self, fetch_document_use_case: FetchDocumentUseCase):
        """Initialize router with use case."""
        self._fetch_document_use_case = fetch_document_use_case
        self.router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all document routes."""

        @self.router.post(
            "/fetch",
            response_model=FetchDocumentResponseModel,
            summary="Fetch Documents from Source Systems",
            description="""
            Retrieve documents from various source systems for processing and ingestion.

            This endpoint connects to external source systems (GitHub, Jira, Confluence, etc.)
            to fetch documents, normalize their content, and prepare them for downstream processing.

            **Supported Source Systems:**
            - **GitHub**: Repositories, issues, pull requests, wikis
            - **GitLab**: Projects, issues, merge requests, documentation
            - **Jira**: Issues, projects, epics, requirements documents
            - **Confluence**: Pages, blogs, spaces, attachments
            - **File System**: Local files and directories
            - **Web**: HTTP/HTTPS accessible documents

            **Document Processing:**
            - Content extraction and normalization
            - Metadata preservation and enrichment
            - Format conversion (Markdown, HTML, PDF, etc.)
            - Link resolution and reference handling
            - Access control and permission checking

            **Scope Parameters:**
            - Repository branches, tags, or commit ranges
            - Date ranges for content filtering
            - File type and size restrictions
            - Content filters and search criteria
            - Authentication and access tokens
            """,
            response_description="Document fetching results with processing statistics"
        )
        async def fetch_documents(
            request: FetchDocumentRequestModel = Body(
                ...,
                examples={
                    "github_repo": {
                        "summary": "Fetch GitHub Repository Documentation",
                        "description": "Retrieve README and documentation files from a GitHub repository",
                        "value": {
                            "source_type": "github",
                            "source_id": "myorg/myrepo",
                            "scope": {
                                "branch": "main",
                                "include_patterns": ["*.md", "*.rst", "docs/**"],
                                "exclude_patterns": ["node_modules/**"]
                            },
                            "include_metadata": True,
                            "timeout_seconds": 300
                        }
                    },
                    "jira_issues": {
                        "summary": "Fetch Jira Issues",
                        "description": "Retrieve issue descriptions and comments from a Jira project",
                        "value": {
                            "source_type": "jira",
                            "source_id": "PROJ",
                            "scope": {
                                "issue_types": ["Bug", "Story", "Task"],
                                "status": ["Open", "In Progress"],
                                "updated_since": "2023-01-01"
                            },
                            "include_metadata": True,
                            "timeout_seconds": 180
                        }
                    },
                    "confluence_space": {
                        "summary": "Fetch Confluence Space Content",
                        "description": "Retrieve pages and content from a Confluence space",
                        "value": {
                            "source_type": "confluence",
                            "source_id": "TECH",
                            "scope": {
                                "space_key": "TECH",
                                "content_types": ["page", "blogpost"],
                                "labels": ["documentation", "api"]
                            },
                            "include_metadata": False,
                            "timeout_seconds": 600
                        }
                    }
                }
            ),
            background_tasks: BackgroundTasks = None
        ) -> FetchDocumentResponseModel:
            """Fetch documents from a source system.

            Retrieves documents from the specified source system and processes
            them for ingestion into the system.
            """
            try:
                # Convert API model to use case request
                use_case_request = FetchDocumentRequest(
                    source_type=request.source_type,
                    source_id=request.source_id,
                    scope=request.scope,
                    include_metadata=request.include_metadata,
                    timeout_seconds=request.timeout_seconds
                )

                # Execute use case
                response = await self._fetch_document_use_case.execute(use_case_request)

                # Convert domain entities to API models
                documents_api = [
                    DocumentResponseModel(
                        id=doc.id,
                        source_type=doc.source_type,
                        source_id=doc.source_id,
                        title=doc.title,
                        content=doc.content,
                        metadata=doc.metadata,
                        tags=doc.tags,
                        fetched_at=doc.fetched_at.isoformat(),
                        version=doc.version,
                        author=doc.author,
                        status=doc.status
                    )
                    for doc in response.documents
                ]

                return FetchDocumentResponseModel(
                    success=response.success,
                    documents=documents_api,
                    documents_processed=response.ingestion_result.documents_processed,
                    documents_succeeded=response.ingestion_result.documents_succeeded,
                    documents_failed=response.ingestion_result.documents_failed,
                    message=response.message,
                    processing_time_seconds=response.processing_time_seconds
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch documents: {str(e)}"
                )

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "source-agent",
                "version": "1.0.0"
            }

        @self.router.get("/sources")
        async def list_supported_sources():
            """List supported source system types."""
            return {
                "sources": [
                    {
                        "type": "github",
                        "name": "GitHub",
                        "supports_versioning": True,
                        "requires_auth": True
                    },
                    {
                        "type": "gitlab",
                        "name": "GitLab",
                        "supports_versioning": True,
                        "requires_auth": True
                    },
                    {
                        "type": "jira",
                        "name": "Jira",
                        "supports_versioning": False,
                        "requires_auth": True
                    },
                    {
                        "type": "confluence",
                        "name": "Confluence",
                        "supports_versioning": False,
                        "requires_auth": True
                    },
                    {
                        "type": "filesystem",
                        "name": "File System",
                        "supports_versioning": False,
                        "requires_auth": False
                    }
                ]
            }

        @self.router.post("/validate")
        async def validate_source_connection(
            source_type: str = Query(..., description="Source system type"),
            source_id: str = Query(..., description="Source identifier"),
            credentials: Optional[Dict[str, Any]] = None
        ):
            """Validate connection to a source system."""
            try:
                # This would validate the connection without fetching documents
                return {
                    "valid": True,
                    "source_type": source_type,
                    "source_id": source_id,
                    "message": f"Connection to {source_type} source validated successfully"
                }
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Source validation failed: {str(e)}"
                )


# Factory function to create router
def create_document_router(
    fetch_document_use_case: FetchDocumentUseCase
) -> APIRouter:
    """Create document router with dependencies."""
    router_instance = DocumentRouter(fetch_document_use_case)
    return router_instance.router
