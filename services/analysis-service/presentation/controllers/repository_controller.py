"""Repository Controller - Handles repository analysis endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ...modules.models import (
    CrossRepositoryAnalysisRequest,
    RepositoryConnectivityRequest,
    RepositoryConnectorConfigRequest
)
from ...modules.analysis_handlers import analysis_handlers


class RepositoryController:
    """Controller for repository-related endpoints."""

    def __init__(self):
        """Initialize controller."""
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("/repositories/analyze")
        async def analyze_repositories_endpoint(req: CrossRepositoryAnalysisRequest):
            """Analyze documentation across multiple repositories.

            Performs comprehensive analysis across multiple repositories to identify
            patterns, inconsistencies, redundancies, and organizational insights.
            """
            return await analysis_handlers.handle_cross_repository_analysis(req)

        @self.router.post("/repositories/connectivity")
        async def analyze_repository_connectivity_endpoint(req: RepositoryConnectivityRequest):
            """Analyze connectivity and dependencies between repositories.

            Examines how repositories are connected through documentation references,
            shared components, and cross-repository dependencies.
            """
            return await analysis_handlers.handle_repository_connectivity(req)

        @self.router.post("/repositories/connectors/config")
        async def configure_repository_connectors_endpoint(req: RepositoryConnectorConfigRequest):
            """Configure repository connectors for external systems.

            Configures connectors and authentication for external repository systems
            including GitHub, GitLab, Azure DevOps, and other version control platforms.
            """
            return await analysis_handlers.handle_repository_connector_config(req)

        @self.router.get("/repositories/connectors")
        async def get_supported_connectors_endpoint():
            """Get list of supported repository connectors.

            Returns comprehensive list of supported repository platforms and
            their configuration requirements and capabilities.
            """
            return await analysis_handlers.handle_supported_connectors()

        @self.router.get("/repositories/frameworks")
        async def get_analysis_frameworks_endpoint():
            """Get available cross-repository analysis frameworks.

            Provides information about available analysis frameworks and methodologies
            for cross-repository documentation analysis and organizational insights.
            """
            return await analysis_handlers.handle_analysis_frameworks()

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for this controller."""
        return self.router
