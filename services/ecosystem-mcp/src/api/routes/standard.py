"""
Standard ecosystem endpoints.

Provides service discovery and relationship information.
"""

import logging
from typing import Dict, List, Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class AboutMeResponse(BaseModel):
    """Service information response."""
    service_name: str = Field(..., description="Name of the service")
    version: str = Field(..., description="Service version")
    description: str = Field(..., description="Service description")
    capabilities: List[str] = Field(..., description="List of capabilities")
    ecosystem_role: str = Field(..., description="Role in ecosystem")
    key_features: List[str] = Field(..., description="Key features")


class EndpointInfo(BaseModel):
    """Endpoint information."""
    path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    description: str = Field(..., description="Endpoint description")
    tags: List[str] = Field(default_factory=list, description="Endpoint tags")


class ServiceRelationship(BaseModel):
    """Service relationship information."""
    service_name: str = Field(..., description="Name of related service")
    relationship: str = Field(..., description="Relationship type: provider, consumer, both")
    description: str = Field(..., description="Description of relationship")


class ProviderConsumerResponse(BaseModel):
    """Provider-consumer relationships."""
    service_name: str = Field(..., description="This service name")
    providers: List[ServiceRelationship] = Field(..., description="Services we consume from")
    consumers: List[ServiceRelationship] = Field(..., description="Services that consume from us")
    both: List[ServiceRelationship] = Field(..., description="Bidirectional relationships")


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/about-me",
    response_model=AboutMeResponse,
    summary="Service information",
    description="Get comprehensive service information and capabilities"
)
async def about_me():
    """
    Get service information.
    
    Returns:
        Comprehensive service description including capabilities,
        role in ecosystem, and key features.
    """
    return AboutMeResponse(
        service_name="Ecosystem MCP",
        version="0.1.0",
        description="Intelligent refactoring knowledge base with MCP integration for AI-powered code analysis and documentation management",
        capabilities=[
            "Document ingestion from Git repositories",
            "Semantic search with vector embeddings",
            "Multi-model LLM routing (Ollama, Claude, Cursor)",
            "Document versioning with Git integration",
            "Real-time job monitoring",
            "Pattern recognition and suggestions",
            "Cost-tracked AI model access",
            "Comprehensive REST API",
            "MCP protocol support for AI agents"
        ],
        ecosystem_role="Central knowledge base for refactoring operations, providing semantic search and AI-powered insights across all refactored services",
        key_features=[
            "Vector storage with ChromaDB for semantic similarity",
            "PostgreSQL for metadata and relationships",
            "Redis Streams for job queueing",
            "Circuit breakers for resilience",
            "Response caching for performance",
            "Prometheus metrics for observability",
            "Rate limiting for protection",
            "Structured logging with request IDs",
            "Graceful degradation when dependencies fail"
        ]
    )


@router.get(
    "/endpoints",
    response_model=List[EndpointInfo],
    summary="List all endpoints",
    description="Get list of all available API endpoints"
)
async def list_endpoints():
    """
    Get list of all service endpoints.
    
    Returns:
        List of endpoints with paths, methods, and descriptions.
    """
    endpoints = [
        # Health & Monitoring
        EndpointInfo(path="/health", method="GET", description="Health check with component status", tags=["Health"]),
        EndpointInfo(path="/metrics", method="GET", description="Prometheus metrics", tags=["Metrics"]),
        
        # Documentation
        EndpointInfo(path="/about-me", method="GET", description="Service information", tags=["Standard"]),
        EndpointInfo(path="/endpoints", method="GET", description="List all endpoints", tags=["Standard"]),
        EndpointInfo(path="/provider-consumer", method="GET", description="Service relationships", tags=["Standard"]),
        EndpointInfo(path="/openapi.json", method="GET", description="OpenAPI specification", tags=["Documentation"]),
        EndpointInfo(path="/docs", method="GET", description="Swagger UI", tags=["Documentation"]),
        EndpointInfo(path="/redoc", method="GET", description="ReDoc documentation", tags=["Documentation"]),
        
        # Core Features
        EndpointInfo(path="/api/v1/search", method="POST", description="Semantic search", tags=["Search"]),
        EndpointInfo(path="/api/v1/query", method="POST", description="Query documents with filters", tags=["Query"]),
        EndpointInfo(path="/api/v1/document/{document_id}", method="GET", description="Get document by ID", tags=["Query"]),
        
        # Admin Operations
        EndpointInfo(path="/api/v1/admin/ingest", method="POST", description="Create ingestion job", tags=["Admin"]),
        EndpointInfo(path="/api/v1/admin/stats", method="GET", description="Service statistics", tags=["Admin"]),
        EndpointInfo(path="/api/v1/admin/queue-status", method="GET", description="Queue status", tags=["Admin"]),
        EndpointInfo(path="/api/v1/admin/cache-stats", method="GET", description="Cache statistics", tags=["Admin"]),
        EndpointInfo(path="/api/v1/admin/circuit-breakers", method="GET", description="Circuit breaker status", tags=["Admin"]),
        
        # Documents
        EndpointInfo(path="/api/v1/documents", method="GET", description="List documents", tags=["Documents"]),
        EndpointInfo(path="/api/v1/documents/{document_id}", method="GET", description="Get specific document", tags=["Documents"]),
        
        # Logs
        EndpointInfo(path="/api/v1/list", method="GET", description="List log files", tags=["Logs"]),
        EndpointInfo(path="/api/v1/tail", method="GET", description="Tail log file", tags=["Logs"]),
        
        # Ollama
        EndpointInfo(path="/api/v1/generate", method="POST", description="Generate text with Ollama", tags=["Ollama"]),
        EndpointInfo(path="/api/v1/embed", method="POST", description="Generate embeddings", tags=["Ollama"]),
        EndpointInfo(path="/api/v1/models", method="GET", description="List Ollama models", tags=["Ollama"]),
    ]
    
    return endpoints


@router.get(
    "/provider-consumer",
    response_model=ProviderConsumerResponse,
    summary="Service relationships",
    description="Get provider-consumer relationships with other services"
)
async def provider_consumer():
    """
    Get service relationships.
    
    Returns:
        Information about which services we provide to,
        which services we consume from, and bidirectional relationships.
    """
    return ProviderConsumerResponse(
        service_name="ecosystem-mcp",
        providers=[
            ServiceRelationship(
                service_name="log-collector-service",
                relationship="provider",
                description="Receives structured logs from ecosystem-mcp"
            )
        ],
        consumers=[
            ServiceRelationship(
                service_name="code-analyzer",
                relationship="consumer",
                description="Consumes semantic search and document query APIs"
            ),
            ServiceRelationship(
                service_name="discovery-agent",
                relationship="consumer",
                description="Consumes semantic search for pattern discovery"
            ),
            ServiceRelationship(
                service_name="bedrock-proxy",
                relationship="consumer",
                description="May consume document context for AI prompts"
            ),
            ServiceRelationship(
                service_name="analysis-service",
                relationship="consumer",
                description="May consume refactoring patterns and documentation"
            )
        ],
        both=[
            ServiceRelationship(
                service_name="PostgreSQL",
                relationship="database",
                description="Primary data store for documents and metadata"
            ),
            ServiceRelationship(
                service_name="Redis",
                relationship="cache-and-queue",
                description="Caching and job queue via Redis Streams"
            ),
            ServiceRelationship(
                service_name="ChromaDB",
                relationship="vector-store",
                description="Vector storage for semantic embeddings"
            ),
            ServiceRelationship(
                service_name="Ollama",
                relationship="llm-provider",
                description="Local LLM for embeddings and text generation"
            )
        ]
    )

