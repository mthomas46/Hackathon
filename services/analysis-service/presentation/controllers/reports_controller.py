"""Reports Controller - Handles report generation endpoints."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from ...modules.models import ReportRequest, NotifyOwnersRequest
from ...modules.report_handlers import report_handlers
from ...modules.analysis_handlers import analysis_handlers


class ReportsController:
    """Controller for report-related endpoints."""

    def __init__(self):
        """Initialize controller."""
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("/reports/generate")
        async def generate_reports_endpoint(req: ReportRequest):
            """Generate various types of reports (summary, trends, etc.).

            Generates comprehensive reports on documentation analysis results
            including quality metrics, trends, risk assessments, and recommendations.
            """
            return await report_handlers.generate_report(req)

        @self.router.get("/findings")
        async def get_findings_endpoint():
            """Retrieve analysis findings with filtering by severity and type.

            Provides filtered access to analysis findings with support for
            severity levels, finding types, date ranges, and document-specific queries.
            """
            return await analysis_handlers.handle_list_findings()

        @self.router.get("/detectors")
        async def get_detectors_endpoint():
            """List available analysis detectors and their capabilities.

            Returns comprehensive information about all available analysis detectors
            including their capabilities, configuration options, and usage guidelines.
            """
            return await analysis_handlers.handle_list_detectors()

        @self.router.get("/reports/confluence/consolidation")
        async def get_confluence_consolidation_report_endpoint():
            """Analyze Confluence pages for duplicates and consolidation opportunities.

            Identifies duplicate content across Confluence pages and provides
            consolidation recommendations to improve documentation organization.
            """
            return await report_handlers.generate_confluence_consolidation_report()

        @self.router.get("/reports/jira/staleness")
        async def get_jira_staleness_report_endpoint():
            """Identify stale Jira tickets requiring review or closure.

            Analyzes Jira tickets for staleness patterns and provides recommendations
            for ticket maintenance and cleanup to improve project tracking efficiency.
            """
            return await report_handlers.generate_jira_staleness_report()

        @self.router.post("/reports/findings/notify-owners")
        async def notify_findings_owners_endpoint(req: NotifyOwnersRequest):
            """Send notifications for findings to document owners.

            Automatically notifies document owners and stakeholders about
            analysis findings requiring their attention and action.
            """
            return await report_handlers.notify_findings_owners(req)

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for this controller."""
        return self.router
