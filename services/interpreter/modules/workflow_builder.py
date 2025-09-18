"""Workflow building functionality for the Interpreter service.

This module contains the WorkflowBuilder class and related functionality,
extracted from the main interpreter service to improve maintainability.
"""

from typing import Dict, Any, Optional, Union, TYPE_CHECKING

from services.shared.integrations.clients.clients import ServiceClients
from services.shared.utilities import utc_now

# Import shared configuration utilities
from .shared_utils import get_default_timeout, get_interpreter_clients

if TYPE_CHECKING:
    from services.interpreter.main import InterpretedWorkflow, WorkflowStep


class WorkflowBuilder:
    """Build workflows from interpreted intents."""

    def __init__(self):
        self.clients = get_interpreter_clients()

    async def build_workflow(self, intent: str, entities: Dict[str, Any]) -> Optional["InterpretedWorkflow"]:
        """Build workflow from intent and entities."""

        if intent == "analyze_document":
            return await self._build_analysis_workflow(entities)
        elif intent == "consistency_check":
            return await self._build_consistency_workflow(entities)
        elif intent == "ingest_github":
            return await self._build_ingestion_workflow("github", entities)
        elif intent == "ingest_jira":
            return await self._build_ingestion_workflow("jira", entities)
        elif intent == "ingest_confluence":
            return await self._build_ingestion_workflow("confluence", entities)
        elif intent == "generate_report":
            return await self._build_report_workflow(entities)
        elif intent == "find_prompt":
            return await self._build_prompt_search_workflow(entities)

        return None

    async def _build_analysis_workflow(self, entities: Dict[str, Any]) -> "InterpretedWorkflow":
        """Build document analysis workflow."""

        targets = []

        if "urls" in entities:
            targets.extend(entities["urls"])
        if "document_ids" in entities:
            targets.extend(entities["document_ids"])

        if not targets:
            # Default to analyzing recent documents
            targets = ["recent"]

        return InterpretedWorkflow(
            workflow_id=f"analysis_{utc_now().strftime('%Y%m%d_%H%M%S')}",
            steps=[
                WorkflowStep(
                    step_id="analyze_docs",
                    service="analysis-service",
                    operation="analyze",
                    params={
                        "targets": targets,
                        "analysis_types": ["consistency", "quality", "security"]
                    }
                ),
                WorkflowStep(
                    step_id="generate_findings",
                    service="analysis-service",
                    operation="findings",
                    params={"format": "json"}
                )
            ]
        )

    async def _build_consistency_workflow(self, entities: Dict[str, Any]) -> "InterpretedWorkflow":
        """Build consistency check workflow."""

        return InterpretedWorkflow(
            workflow_id=f"consistency_{utc_now().strftime('%Y%m%d_%H%M%S')}",
            steps=[
                WorkflowStep(
                    step_id="consistency_check",
                    service="analysis-service",
                    operation="consistency/check",
                    params={"comprehensive": True}
                )
            ]
        )

    async def _build_ingestion_workflow(self, source_type: str, entities: Dict[str, Any]) -> "InterpretedWorkflow":
        """Build data ingestion workflow."""

        sources = []

        if source_type == "github" and "repo" in entities:
            sources.extend([f"github:{repo}" for repo in entities["repo"]])
        elif source_type == "jira" and "jira_key" in entities:
            sources.extend([f"jira:{key}" for key in entities["jira_key"]])
        elif source_type == "confluence" and "url" in entities:
            sources.extend(entities["url"])

        if not sources:
            sources = [f"{source_type}:default"]

        return InterpretedWorkflow(
            workflow_id=f"ingest_{source_type}_{utc_now().strftime('%Y%m%d_%H%M%S')}",
            steps=[
                WorkflowStep(
                    step_id="ingest_data",
                    service="source-agent",
                    operation="ingest",
                    params={
                        "sources": sources,
                        "source_type": source_type
                    }
                ),
                WorkflowStep(
                    step_id="store_documents",
                    service="doc_store",
                    operation="store",
                    params={"validate": True}
                )
            ]
        )

    async def _build_report_workflow(self, entities: Dict[str, Any]) -> "InterpretedWorkflow":
        """Build report generation workflow."""

        report_type = entities.get("report_type", ["summary"])[0]

        return InterpretedWorkflow(
            workflow_id=f"report_{utc_now().strftime('%Y%m%d_%H%M%S')}",
            steps=[
                WorkflowStep(
                    step_id="generate_report",
                    service="analysis-service",
                    operation="reports/generate",
                    params={
                        "type": report_type,
                        "format": "json"
                    }
                )
            ]
        )

    async def _build_prompt_search_workflow(self, entities: Dict[str, Any]) -> "InterpretedWorkflow":
        """Build prompt search workflow."""

        search_terms = entities.get("search_terms", [""])

        return InterpretedWorkflow(
            workflow_id=f"prompt_search_{utc_now().strftime('%Y%m%d_%H%M%S')}",
            steps=[
                WorkflowStep(
                    step_id="search_prompts",
                    service="prompt-store",
                    operation="search",
                    params={
                        "query": " ".join(search_terms),
                        "limit": 10
                    }
                )
            ]
        )
