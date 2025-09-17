"""PR Confidence Controller - Handles PR confidence analysis endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ...modules.pr_confidence_analysis import pr_confidence_analyzer


class PRConfidenceController:
    """Controller for PR confidence analysis endpoints."""

    def __init__(self):
        """Initialize controller."""
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("/pr-confidence/analyze")
        async def analyze_pr_confidence_endpoint(request: Dict[str, Any]):
            """Analyze PR confidence based on documentation changes.

            Performs comprehensive analysis of pull request changes to assess
            documentation quality, completeness, and potential impact.
            """
            return await pr_confidence_analyzer.analyze_pr_confidence(request)

        @self.router.get("/pr-confidence/history/{pr_id}")
        async def get_pr_confidence_history_endpoint(pr_id: str):
            """Get PR confidence analysis history.

            Retrieves historical confidence analysis data for a specific
            pull request including trends and improvement recommendations.
            """
            return await pr_confidence_analyzer.get_pr_confidence_history(pr_id)

        @self.router.get("/pr-confidence/statistics")
        async def get_pr_confidence_statistics_endpoint():
            """Get PR confidence analysis statistics.

            Provides comprehensive statistics about PR confidence analysis
            including success rates, common issues, and improvement trends.
            """
            return await pr_confidence_analyzer.get_pr_confidence_statistics()

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for this controller."""
        return self.router
