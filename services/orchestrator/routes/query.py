"""Query Routes for Orchestrator Service"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, List
import httpx
import json
import os

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v:
            raise ValueError('Query cannot be empty')
        if len(v) > 5000:
            raise ValueError('Query too long (max 5000 characters)')
        return v

@router.post("/query")
async def process_query(req: QueryRequest):
    """Process natural language query."""
    return {
        "query": req.query,
        "interpreted_intent": "search_documents",
        "confidence": 0.85,
        "results": []
    }

@router.post("/query/execute")
async def execute_query(req: QueryRequest):
    """Execute interpreted query."""
    return {
        "query": req.query,
        "status": "executed",
        "results": {
            "documents_found": 5,
            "services_used": ["doc_store", "analyzer"]
        }
    }

# ============================================================================
# SIMULATION ENDPOINTS
# ============================================================================

class SimulationRequest(BaseModel):
    """Request model for simulation creation."""
    query: str
    context: Optional[Dict[str, Any]] = {}
    simulation_config: Optional[Dict[str, Any]] = {}
    generate_mock_data: Optional[bool] = True
    analysis_types: Optional[List[str]] = ["document_analysis", "timeline_analysis"]

    @field_validator('query')
    @classmethod
    def validate_simulation_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Simulation query cannot be empty')
        if len(v) > 2000:
            raise ValueError('Query too long (max 2000 characters)')
        return v.strip()

class MockDataRequest(BaseModel):
    """Request model for mock data generation."""
    query: str
    context: Optional[Dict[str, Any]] = {}
    data_types: Optional[List[str]] = ["documents", "team_members", "timeline"]

class AnalysisRequest(BaseModel):
    """Request model for analysis operations."""
    content: str
    analysis_type: str = "general"
    context: Optional[Dict[str, Any]] = {}

@router.post("/simulation/create")
async def create_simulation_via_orchestrator(req: SimulationRequest):
    """Create and execute a simulation based on natural language query."""
    try:
        # Get project simulation service URL from service registry
        simulation_service_url = await get_simulation_service_url()

        if not simulation_service_url:
            raise HTTPException(
                status_code=503,
                detail="Project simulation service not available"
            )

        # Prepare request for simulation service
        simulation_request = {
            "query": req.query,
            "context": req.context,
            "simulation_config": req.simulation_config or {
                "type": "web_application",
                "complexity": "medium",
                "duration_weeks": 8,
                "team_size": 5
            }
        }

        # Call simulation service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{simulation_service_url}/api/v1/interpreter/simulate",
                json=simulation_request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Simulation service error: {response.text}"
                )

            result = response.json()

            return {
                "orchestrator_request_id": "sim_" + str(hash(req.query))[:8],
                "simulation_service_response": result,
                "query_processed": req.query,
                "mock_data_generated": req.generate_mock_data,
                "analysis_performed": req.analysis_types
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create simulation: {str(e)}"
        )

@router.post("/simulation/mock-data")
async def generate_mock_data_via_orchestrator(req: MockDataRequest):
    """Generate mock data for simulation without creating full simulation."""
    try:
        # Get project simulation service URL
        simulation_service_url = await get_simulation_service_url()

        if not simulation_service_url:
            raise HTTPException(
                status_code=503,
                detail="Project simulation service not available"
            )

        # Prepare request for simulation service
        mock_data_request = {
            "query": req.query,
            "context": req.context,
            "data_types": req.data_types
        }

        # Call simulation service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{simulation_service_url}/api/v1/interpreter/mock-data",
                json=mock_data_request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Simulation service error: {response.text}"
                )

            result = response.json()

            return {
                "orchestrator_request_id": "mock_" + str(hash(req.query))[:8],
                "mock_data": result.get("data", {}).get("mock_data", {}),
                "data_types_generated": req.data_types,
                "query_processed": req.query
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate mock data: {str(e)}"
        )

@router.post("/simulation/analyze")
async def analyze_via_simulation_service(req: AnalysisRequest):
    """Perform analysis using simulation service infrastructure."""
    try:
        # Get project simulation service URL
        simulation_service_url = await get_simulation_service_url()

        if not simulation_service_url:
            raise HTTPException(
                status_code=503,
                detail="Project simulation service not available"
            )

        # Prepare request for simulation service
        analysis_request = {
            "content": req.content,
            "analysis_type": req.analysis_type,
            "context": req.context
        }

        # Call simulation service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{simulation_service_url}/api/v1/interpreter/analyze",
                json=analysis_request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Simulation service error: {response.text}"
                )

            result = response.json()

            return {
                "orchestrator_request_id": "analysis_" + str(hash(req.content))[:8],
                "analysis_result": result.get("data", {}).get("analysis_result", {}),
                "analysis_type": req.analysis_type,
                "content_length": len(req.content)
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform analysis: {str(e)}"
        )

@router.get("/simulation/capabilities")
async def get_simulation_capabilities_via_orchestrator():
    """Get simulation capabilities from the project simulation service."""
    try:
        # Get project simulation service URL
        simulation_service_url = await get_simulation_service_url()

        if not simulation_service_url:
            raise HTTPException(
                status_code=503,
                detail="Project simulation service not available"
            )

        # Call simulation service capabilities endpoint
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{simulation_service_url}/api/v1/interpreter/capabilities"
            )

            if response.status_code != 200:
                # Return basic capabilities if service call fails
                return {
                    "orchestrator_capabilities": {
                        "simulation_types": ["web_application", "api_service", "data_pipeline"],
                        "complexity_levels": ["low", "medium", "high"],
                        "analysis_types": ["document_analysis", "timeline_analysis", "team_dynamics"],
                        "mock_data_generation": True,
                        "service_status": "orchestrator_fallback"
                    }
                }

            result = response.json()
            return {
                "orchestrator_capabilities": result.get("data", {}),
                "service_status": "simulation_service_connected"
            }

    except HTTPException:
        raise
    except Exception as e:
        # Return fallback capabilities
        return {
            "orchestrator_capabilities": {
                "simulation_types": ["web_application", "api_service"],
                "complexity_levels": ["low", "medium"],
                "analysis_types": ["document_analysis", "timeline_analysis"],
                "mock_data_generation": True,
                "service_status": "orchestrator_fallback",
                "error": str(e)
            }
        }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _detect_docker_environment() -> bool:
    """Detect if the service is running in a Docker container."""
    docker_indicators = [
        os.path.exists('/.dockerenv'),
        os.path.exists('/proc/1/cgroup') and 'docker' in open('/proc/1/cgroup').read() if os.path.exists('/proc/1/cgroup') else False,
        (os.getenv('DOCKER_CONTAINER') or '').lower() in ('true', '1', 'yes'),
        os.getenv('DOCKER_HOST') is not None,
        (os.getenv('HOSTNAME') or '').startswith('docker-')
    ]
    return any(docker_indicators)

def _get_simulation_service_url() -> str:
    """Get the appropriate simulation service URL based on environment."""
    # Check for explicit override
    override_url = os.getenv("PROJECT_SIMULATION_URL")
    if override_url:
        return override_url

    # Determine environment and return appropriate URL
    # Based on docker-compose.dev.yml: project-simulation uses port 5075
    is_docker = _detect_docker_environment()
    if is_docker:
        return "http://project-simulation:5075"
    else:
        return "http://localhost:5075"

async def get_simulation_service_url() -> Optional[str]:
    """Get the URL of the project simulation service from service registry."""
    try:
        service_url = _get_simulation_service_url()

        # Basic connectivity check
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/health")
            if response.status_code == 200:
                return service_url

        return None

    except Exception:
        # Service not available
        return None
