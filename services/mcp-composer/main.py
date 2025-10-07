"""MCP Composer Service - Main FastAPI application."""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import uvicorn
import redis.asyncio as redis
from contextlib import asynccontextmanager

from services.mcp_composer.infrastructure.config.settings import get_settings
from services.mcp_composer.infrastructure.repositories.redis_composition_repository import (
    RedisCompositionRepository
)
from services.mcp_composer.domain.repositories.composition_repository import (
    EntityNotFoundError,
    DuplicateEntityError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Settings
settings = get_settings()

# Global repository (will be initialized on startup)
composition_repository: Optional[RedisCompositionRepository] = None
redis_client: Optional[redis.Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    global composition_repository, redis_client
    
    # Startup
    logger.info("Starting MCP Composer Service...")
    
    # Initialize Redis
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
        decode_responses=False,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
    )
    
    # Test Redis connection
    try:
        await redis_client.ping()
        logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    
    # Initialize repository
    composition_repository = RedisCompositionRepository(
        redis_client=redis_client,
        key_prefix=settings.redis_key_prefix
    )
    
    logger.info("MCP Composer Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Composer Service...")
    if redis_client:
        await redis_client.close()
    logger.info("MCP Composer Service stopped")


# Create FastAPI app
app = FastAPI(
    title="MCP Composer Service",
    description="Multi-MCP composition and orchestration service for the MCP ecosystem",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)


def get_repository() -> RedisCompositionRepository:
    """Get the composition repository dependency."""
    if composition_repository is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Repository not initialized"
        )
    return composition_repository


# Request/Response Models
class ComposeQueryRequest(BaseModel):
    """Request to compose and query multiple MCPs."""
    query: str = Field(..., description="The user query")
    composition_id: Optional[str] = Field(None, description="Composition to use")
    composition_yaml: Optional[str] = Field(None, description="Inline composition YAML")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ComposeQueryResponse(BaseModel):
    """Response from composed MCP query."""
    query: str
    composition_id: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    resolution_strategy: str
    mcp_responses: List[Dict[str, Any]]
    elapsed_ms: float


class CreateCompositionRequest(BaseModel):
    """Request to create a new composition."""
    yaml_content: str = Field(..., description="mcp-compose.yaml content")


class CompositionResponse(BaseModel):
    """Response with composition details."""
    composition_id: str
    name: str
    description: str
    strategy: str
    conflict_resolution: str
    num_mcps: int
    mcps: List[Dict[str, Any]]


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mcp-composer",
        "version": "1.0.0"
    }


# Composition management endpoints
@app.post("/api/v1/compositions", response_model=CompositionResponse, tags=["Compositions"], status_code=status.HTTP_201_CREATED)
async def create_composition(
    request: CreateCompositionRequest,
    repository: RedisCompositionRepository = Depends(get_repository)
):
    """
    Create a new MCP composition from YAML.
    
    Upload an mcp-compose.yaml specification to define how multiple MCPs
    should work together.
    """
    logger.info("Creating new composition from YAML")
    
    try:
        from infrastructure.parsers.yaml_parser import MCPComposeYAMLParser
        import yaml
        
        parser = MCPComposeYAMLParser()
        yaml_data = yaml.safe_load(request.yaml_content)
        composition = parser.parse_dict(yaml_data)
        
        # Save to repository
        try:
            await repository.save(composition)
        except DuplicateEntityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Composition {composition.composition_id} already exists"
            )
        
        logger.info(f"Created composition: {composition.composition_id}")
        
        return CompositionResponse(
            composition_id=composition.composition_id,
            name=composition.name,
            description=composition.description,
            strategy=composition.strategy.value,
            conflict_resolution=composition.conflict_resolution.value,
            num_mcps=len(composition.mcps),
            mcps=[
                {
                    "mcp_id": m.mcp_id,
                    "tier": m.tier,
                    "priority": m.priority,
                    "weight": m.weight
                }
                for m in composition.mcps
            ]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create composition: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid composition YAML: {str(e)}"
        )


@app.get("/api/v1/compositions/{composition_id}", response_model=CompositionResponse, tags=["Compositions"])
async def get_composition(
    composition_id: str,
    repository: RedisCompositionRepository = Depends(get_repository)
):
    """Get composition details by ID."""
    logger.info(f"Getting composition: {composition_id}")
    
    try:
        composition = await repository.get_by_id(composition_id)
        
        if not composition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Composition {composition_id} not found"
            )
        
        return CompositionResponse(
            composition_id=composition.composition_id,
            name=composition.name,
            description=composition.description,
            strategy=composition.strategy.value,
            conflict_resolution=composition.conflict_resolution.value,
            num_mcps=len(composition.mcps),
            mcps=[
                {
                    "mcp_id": m.mcp_id,
                    "tier": m.tier,
                    "priority": m.priority,
                    "weight": m.weight
                }
                for m in composition.mcps
            ]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get composition {composition_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve composition: {str(e)}"
        )


@app.get("/api/v1/compositions", tags=["Compositions"])
async def list_compositions(
    active_only: bool = False,
    repository: RedisCompositionRepository = Depends(get_repository)
):
    """List all compositions."""
    logger.info(f"Listing compositions (active_only={active_only})")
    
    try:
        if active_only:
            compositions = await repository.get_active()
        else:
            compositions = await repository.get_all()
        
        return {
            "compositions": [
                {
                    "composition_id": c.composition_id,
                    "name": c.name,
                    "description": c.description,
                    "strategy": c.strategy.value,
                    "conflict_resolution": c.conflict_resolution.value,
                    "num_mcps": len(c.mcps),
                    "is_active": c.is_active,
                    "execution_count": c.execution_count,
                    "success_rate": c.get_success_rate(),
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat()
                }
                for c in compositions
            ],
            "count": len(compositions)
        }
    
    except Exception as e:
        logger.error(f"Failed to list compositions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list compositions: {str(e)}"
        )


@app.put("/api/v1/compositions/{composition_id}", response_model=CompositionResponse, tags=["Compositions"])
async def update_composition(
    composition_id: str,
    request: CreateCompositionRequest,
    repository: RedisCompositionRepository = Depends(get_repository)
):
    """Update an existing composition."""
    logger.info(f"Updating composition: {composition_id}")
    
    try:
        # Check if composition exists
        existing = await repository.get_by_id(composition_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Composition {composition_id} not found"
            )
        
        # Parse new YAML
        from infrastructure.parsers.yaml_parser import MCPComposeYAMLParser
        import yaml
        
        parser = MCPComposeYAMLParser()
        yaml_data = yaml.safe_load(request.yaml_content)
        composition = parser.parse_dict(yaml_data)
        
        # Preserve the original ID
        composition.composition_id = composition_id
        composition.created_at = existing.created_at
        
        # Update in repository
        try:
            await repository.update(composition)
        except EntityNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Composition {composition_id} not found"
            )
        
        logger.info(f"Updated composition: {composition_id}")
        
        return CompositionResponse(
            composition_id=composition.composition_id,
            name=composition.name,
            description=composition.description,
            strategy=composition.strategy.value,
            conflict_resolution=composition.conflict_resolution.value,
            num_mcps=len(composition.mcps),
            mcps=[
                {
                    "mcp_id": m.mcp_id,
                    "tier": m.tier,
                    "priority": m.priority,
                    "weight": m.weight
                }
                for m in composition.mcps
            ]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update composition {composition_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid composition YAML: {str(e)}"
        )


@app.delete("/api/v1/compositions/{composition_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Compositions"])
async def delete_composition(
    composition_id: str,
    repository: RedisCompositionRepository = Depends(get_repository)
):
    """Delete a composition by ID."""
    logger.info(f"Deleting composition: {composition_id}")
    
    try:
        await repository.delete(composition_id)
        logger.info(f"Deleted composition: {composition_id}")
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composition {composition_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to delete composition {composition_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete composition: {str(e)}"
        )


# Query execution endpoints
@app.post("/api/v1/compose/query", response_model=ComposeQueryResponse, tags=["Query"])
async def compose_query(
    request: ComposeQueryRequest,
    repository: RedisCompositionRepository = Depends(get_repository)
):
    """
    Execute a query across multiple MCPs using composition.
    
    This endpoint routes the query to multiple MCPs according to the
    composition strategy, resolves any conflicts, and returns a unified answer.
    """
    logger.info(f"Composing query: {request.query[:100]}...")
    
    try:
        from domain.services.routing_engine import RoutingEngine
        from domain.services.conflict_resolver import ConflictResolver
        from infrastructure.parsers.yaml_parser import MCPComposeYAMLParser
        import yaml
        
        # Parse or load composition
        if request.composition_yaml:
            parser = MCPComposeYAMLParser()
            yaml_data = yaml.safe_load(request.composition_yaml)
            composition = parser.parse_dict(yaml_data)
        elif request.composition_id:
            # Load from repository
            composition = await repository.get_by_id(request.composition_id)
            if not composition:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Composition {request.composition_id} not found"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either composition_id or composition_yaml"
            )
        
        # Route query to MCPs
        router = RoutingEngine()
        routing_result = await router.route_query(
            request.query,
            composition,
            request.context
        )
        
        # Resolve conflicts
        resolver = ConflictResolver()
        resolved = resolver.resolve(
            routing_result["mcp_responses"],
            composition
        )
        
        await router.close()
        
        # Update execution stats if composition was loaded from repository
        if request.composition_id:
            try:
                composition.increment_execution(success=True)
                await repository.update(composition)
            except Exception as e:
                logger.warning(f"Failed to update composition stats: {e}")
        
        return ComposeQueryResponse(
            query=request.query,
            composition_id=composition.composition_id,
            answer=resolved["answer"],
            confidence=resolved["confidence"],
            sources=resolved.get("sources", []),
            resolution_strategy=resolved["resolution_strategy"],
            mcp_responses=resolved.get("all_responses", []),
            elapsed_ms=routing_result["elapsed_ms"]
        )
    
    except Exception as e:
        logger.error(f"Query composition failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )


# Example composition endpoint
@app.get("/api/v1/examples/composition", tags=["Examples"])
async def get_example_composition():
    """Get an example mcp-compose.yaml file."""
    from infrastructure.parsers.yaml_parser import create_example_composition
    
    return {
        "yaml": create_example_composition(),
        "description": "Example multi-tier MCP composition"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5646,
        reload=True,
        log_level="info"
    )
