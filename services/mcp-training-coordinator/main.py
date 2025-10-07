"""Main FastAPI application for Training Coordinator Service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from services.training_coordinator import __version__, __service_name__
from services.training_coordinator.infrastructure.config.settings import get_settings
from services.training_coordinator.infrastructure.repositories.redis_job_repository import RedisJobRepository
from services.training_coordinator.presentation import dependencies
from services.training_coordinator.application.dto.create_job_request import CreateJobRequest
from services.training_coordinator.application.dto.execute_job_request import ExecuteJobRequest
from services.training_coordinator.application.dto.job_response import JobResponse
from services.training_coordinator.application.use_cases.create_job_use_case import CreateJobUseCase
from services.training_coordinator.application.use_cases.get_job_use_case import GetJobUseCase
from services.training_coordinator.application.use_cases.execute_job_use_case import ExecuteJobUseCase
from services.training_coordinator.domain.value_objects.data_source import DataSource
from services.training_coordinator.domain.value_objects.job_priority import JobPriority

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Global instances
redis_client: redis.Redis = None
job_repository: RedisJobRepository = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    # Startup
    logger.info(f"Starting {__service_name__} v{__version__}")
    
    global redis_client, job_repository
    
    try:
        # Initialize Redis
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=False
        )
        await redis_client.ping()
        logger.info("Redis connection established")
        
        # Initialize repository
        job_repository = RedisJobRepository(redis_client, settings.redis_key_prefix)
        logger.info("Job repository initialized")
        
        # Initialize dependencies
        dependencies.init_dependencies(redis_client, job_repository)
        logger.info(f"{__service_name__} startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    
    finally:
        # Shutdown
        logger.info(f"Shutting down {__service_name__}")
        if redis_client:
            await redis_client.close()
        logger.info(f"{__service_name__} shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Training Coordinator Service",
    description="Orchestrates MCP training pipeline with job management and worker coordination",
    version=__version__,
    docs_url=settings.docs_url,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        await redis_client.ping()
        return {"status": "healthy", "service": __service_name__, "version": __version__}
    except:
        return {"status": "unhealthy"}


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": __service_name__,
        "version": __version__,
        "status": "operational",
        "capabilities": [
            "job_creation",
            "job_execution",
            "worker_orchestration",
            "pipeline_management",
        ]
    }


# Job endpoints
@app.post(
    f"{settings.api_prefix}/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Jobs"]
)
async def create_job(
    mcp_id: str,
    name: str,
    description: str,
    data_sources: list[str],
    use_case: CreateJobUseCase = Depends(dependencies.get_create_job_use_case)
):
    """Create a new training job."""
    try:
        request = CreateJobRequest(
            mcp_id=mcp_id,
            name=name,
            description=description,
            data_sources=[DataSource(ds) for ds in data_sources],
            priority=JobPriority.NORMAL,
        )
        return await use_case.execute(request)
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    f"{settings.api_prefix}/jobs/{{job_id}}",
    response_model=JobResponse,
    tags=["Jobs"]
)
async def get_job(
    job_id: str,
    use_case: GetJobUseCase = Depends(dependencies.get_get_job_use_case)
):
    """Get job by ID."""
    job = await use_case.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post(
    f"{settings.api_prefix}/jobs/{{job_id}}/execute",
    response_model=JobResponse,
    tags=["Jobs"]
)
async def execute_job(
    job_id: str,
    use_case: ExecuteJobUseCase = Depends(dependencies.get_execute_job_use_case)
):
    """Execute a training job."""
    try:
        request = ExecuteJobRequest(job_id=job_id)
        return await use_case.execute(request)
    except Exception as e:
        logger.error(f"Error executing job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )

