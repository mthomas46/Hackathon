"""Integration Controller - Handles integration endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ...modules.integration_handlers import integration_handlers


class IntegrationController:
    """Controller for integration-related endpoints."""

    def __init__(self):
        """Initialize controller."""
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.get("/integration/health")
        async def get_integration_health_endpoint():
            """Check integration health with other services.

            Provides comprehensive health status for all service integrations
            including connectivity, response times, and error rates.
            """
            return await integration_handlers.get_integration_health()

        @self.router.post("/integration/analyze-with-prompt")
        async def analyze_with_prompt_endpoint(request: Dict[str, Any]):
            """Analyze using prompts from Prompt Store.

            Performs analysis using customizable prompts from the Prompt Store
            service, enabling flexible and context-aware analysis workflows.
            """
            return await integration_handlers.analyze_with_prompt(request)

        @self.router.post("/integration/natural-language-analysis")
        async def natural_language_analysis_endpoint(request: Dict[str, Any]):
            """Analyze using natural language queries.

            Processes natural language queries to perform intelligent analysis
            and provide human-readable insights and recommendations.
            """
            return await integration_handlers.natural_language_analysis(request)

        @self.router.get("/integration/prompts/categories")
        async def get_prompt_categories_endpoint():
            """Get available prompt categories.

            Returns list of available prompt categories and templates
            for different types of analysis and use cases.
            """
            return await integration_handlers.get_prompt_categories()

        @self.router.post("/integration/log-analysis")
        async def log_analysis_usage_endpoint(request: Dict[str, Any]):
            """Log analysis usage for analytics.

            Records analysis usage patterns for analytics and optimization
            of the analysis service based on actual usage patterns.
            """
            return await integration_handlers.log_analysis_usage(request)

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for this controller."""
        return self.router
