"""MCP Composer Service - Main FastAPI application."""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP Composer Service",
    description="Multi-MCP composition and orchestration service for the MCP ecosystem",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)


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
@app.post("/api/v1/compositions", response_model=CompositionResponse, tags=["Compositions"])
async def create_composition(request: CreateCompositionRequest):
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
        
        # TODO: Save to repository
        
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
    
    except Exception as e:
        logger.error(f"Failed to create composition: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid composition YAML: {str(e)}"
        )


@app.get("/api/v1/compositions/{composition_id}", response_model=CompositionResponse, tags=["Compositions"])
async def get_composition(composition_id: str):
    """Get composition details by ID."""
    # TODO: Implement retrieval from repository
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not yet implemented"
    )


@app.get("/api/v1/compositions", tags=["Compositions"])
async def list_compositions():
    """List all compositions."""
    # TODO: Implement listing from repository
    return {
        "compositions": [],
        "count": 0
    }


# Query execution endpoints
@app.post("/api/v1/compose/query", response_model=ComposeQueryResponse, tags=["Query"])
async def compose_query(request: ComposeQueryRequest):
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
            # TODO: Load from repository
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Loading saved compositions not yet implemented"
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
