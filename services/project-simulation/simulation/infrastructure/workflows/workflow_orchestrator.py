"""Workflow Orchestrator - Cross-Service Workflow Coordination.

This module provides workflow orchestration capabilities that integrate
with the ecosystem orchestrator service for complex cross-service workflows.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))
from integrations.orchestration.orchestration import WorkflowOrchestrator

from ..logging import get_simulation_logger
from ..clients.ecosystem_clients import (
    get_orchestrator_client,
    get_doc_store_client,
    get_mock_data_generator_client,
    get_analysis_service_client,
    get_llm_gateway_client
)


class SimulationWorkflowOrchestrator:
    """Orchestrator for simulation-related workflows."""

    def __init__(self):
        """Initialize workflow orchestrator."""
        self.logger = get_simulation_logger()
        self.orchestrator_client = get_orchestrator_client()
        self.doc_store_client = get_doc_store_client()
        self.mock_data_client = get_mock_data_generator_client()
        self.analysis_client = get_analysis_service_client()
        self.llm_client = get_llm_gateway_client()

    async def orchestrate_document_generation_workflow(
        self, simulation_id: str, project_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Orchestrate document generation workflow."""
        start_time = datetime.now()

        try:
            self.logger.info(
                "Starting document generation workflow",
                simulation_id=simulation_id,
                workflow_type="document_generation"
            )

            # Step 1: Generate project documents
            project_docs = await self.mock_data_client.generate_project_documents({
                "project_name": project_config["name"],
                "project_type": project_config["type"],
                "team_size": project_config["team_size"],
                "complexity": project_config["complexity"],
                "duration_weeks": project_config["duration_weeks"],
                "document_types": ["project_requirements", "architecture_diagram"]
            })

            # Step 2: Generate user stories
            user_stories = await self.mock_data_client.generate_project_documents({
                "project_name": project_config["name"],
                "project_type": project_config["type"],
                "team_size": project_config["team_size"],
                "complexity": project_config["complexity"],
                "document_types": ["user_story"]
            })

            # Step 3: Store documents in doc_store
            stored_docs = []
            all_docs = project_docs.get("documents_created", []) + user_stories.get("documents_created", [])

            for doc in all_docs:
                doc_id = await self.doc_store_client.store_document(
                    title=doc.get("title", "Generated Document"),
                    content=str(doc.get("content", "")),
                    metadata={
                        "simulation_id": simulation_id,
                        "document_type": doc.get("type", "unknown"),
                        "generated_at": datetime.now().isoformat()
                    }
                )
                if doc_id:
                    stored_docs.append(doc_id)

            # Step 4: Analyze generated documents
            if all_docs:
                analysis_result = await self.analysis_client.analyze_documents(all_docs)

                # Generate insights using LLM
                insights_prompt = f"""
                Analyze the following project documentation and provide key insights:

                Project: {project_config['name']}
                Documents Generated: {len(all_docs)}
                Document Types: {[doc.get('type') for doc in all_docs]}

                Analysis Results: {analysis_result}

                Provide insights about:
                1. Documentation completeness
                2. Potential gaps or inconsistencies
                3. Quality assessment
                4. Recommendations for improvement
                """

                llm_response = await self.llm_client.generate_content(insights_prompt)
                insights = llm_response.get("content", "No insights generated")

            else:
                insights = "No documents were generated for analysis"

            execution_time = (datetime.now() - start_time).total_seconds()

            result = {
                "success": True,
                "workflow_type": "document_generation",
                "execution_time_seconds": execution_time,
                "documents_generated": len(all_docs),
                "documents_stored": len(stored_docs),
                "insights": insights,
                "stored_document_ids": stored_docs
            }

            self.logger.info(
                "Document generation workflow completed",
                simulation_id=simulation_id,
                documents_generated=len(all_docs),
                execution_time_seconds=execution_time
            )

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                "Document generation workflow failed",
                error=str(e),
                simulation_id=simulation_id,
                execution_time_seconds=execution_time
            )

            return {
                "success": False,
                "workflow_type": "document_generation",
                "execution_time_seconds": execution_time,
                "error": str(e)
            }

    async def orchestrate_team_dynamics_workflow(
        self, simulation_id: str, team_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Orchestrate team dynamics analysis workflow."""
        start_time = datetime.now()

        try:
            self.logger.info(
                "Starting team dynamics workflow",
                simulation_id=simulation_id,
                workflow_type="team_dynamics"
            )

            # Generate team activities
            activities_result = await self.mock_data_client.generate_team_activities({
                "project_name": team_data.get("project_name", "Unknown Project"),
                "team_members": team_data.get("members", []),
                "activity_types": ["code_commit", "meeting_notes", "design_decision"],
                "time_range_days": 30,
                "activity_count": 20
            })

            # Analyze team dynamics based on activities
            activities = activities_result.get("documents_created", [])

            # Use LLM to analyze team dynamics
            dynamics_prompt = f"""
            Analyze the following team activities and assess team dynamics:

            Team Size: {len(team_data.get('members', []))}
            Activities Analyzed: {len(activities)}
            Activity Types: {[a.get('type') for a in activities]}

            Activity Summary:
            {chr(10).join([f"- {a.get('title', 'Unknown')}: {a.get('description', '')}" for a in activities[:10]])}

            Provide analysis of:
            1. Team collaboration patterns
            2. Communication effectiveness
            3. Work distribution and balance
            4. Potential bottlenecks or issues
            5. Recommendations for improvement
            """

            llm_response = await self.llm_client.generate_content(dynamics_prompt)
            dynamics_analysis = llm_response.get("content", "No analysis generated")

            execution_time = (datetime.now() - start_time).total_seconds()

            result = {
                "success": True,
                "workflow_type": "team_dynamics",
                "execution_time_seconds": execution_time,
                "activities_analyzed": len(activities),
                "team_size": len(team_data.get("members", [])),
                "dynamics_analysis": dynamics_analysis,
                "recommendations": self._extract_recommendations(dynamics_analysis)
            }

            self.logger.info(
                "Team dynamics workflow completed",
                simulation_id=simulation_id,
                activities_analyzed=len(activities),
                execution_time_seconds=execution_time
            )

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                "Team dynamics workflow failed",
                error=str(e),
                simulation_id=simulation_id,
                execution_time_seconds=execution_time
            )

            return {
                "success": False,
                "workflow_type": "team_dynamics",
                "execution_time_seconds": execution_time,
                "error": str(e)
            }

    async def orchestrate_full_simulation_workflow(
        self, simulation_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Orchestrate complete simulation workflow with all phases."""
        start_time = datetime.now()

        try:
            self.logger.info(
                "Starting full simulation workflow",
                simulation_id=simulation_id,
                workflow_type="full_simulation"
            )

            workflow_results = []

            # Phase 1: Document Generation
            if config.get("include_document_generation", True):
                doc_result = await self.orchestrate_document_generation_workflow(
                    simulation_id, config.get("project_config", {})
                )
                workflow_results.append(doc_result)

            # Phase 2: Team Dynamics Analysis
            if config.get("include_team_dynamics", True):
                team_result = await self.orchestrate_team_dynamics_workflow(
                    simulation_id, config.get("team_config", {})
                )
                workflow_results.append(team_result)

            # Phase 3: Timeline Event Generation
            if config.get("include_timeline_events", True):
                timeline_result = await self.mock_data_client.generate_timeline_events({
                    "project_name": config.get("project_config", {}).get("name", "Unknown"),
                    "timeline_phases": config.get("timeline_phases", []),
                    "include_past_events": True,
                    "include_future_events": False
                })
                workflow_results.append({
                    "success": timeline_result.get("success", False),
                    "workflow_type": "timeline_events",
                    "execution_time_seconds": 0.5,  # Mock execution time
                    "events_generated": len(timeline_result.get("documents_created", []))
                })

            # Calculate overall results
            successful_workflows = sum(1 for r in workflow_results if r.get("success", False))
            total_execution_time = sum(r.get("execution_time_seconds", 0) for r in workflow_results)

            result = {
                "success": successful_workflows == len(workflow_results),
                "workflow_type": "full_simulation",
                "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
                "workflows_executed": len(workflow_results),
                "workflows_succeeded": successful_workflows,
                "total_sub_execution_time": total_execution_time,
                "workflow_results": workflow_results,
                "overall_efficiency": successful_workflows / len(workflow_results) if workflow_results else 0
            }

            self.logger.info(
                "Full simulation workflow completed",
                simulation_id=simulation_id,
                workflows_executed=len(workflow_results),
                workflows_succeeded=successful_workflows,
                execution_time_seconds=result["execution_time_seconds"]
            )

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                "Full simulation workflow failed",
                error=str(e),
                simulation_id=simulation_id,
                execution_time_seconds=execution_time
            )

            return {
                "success": False,
                "workflow_type": "full_simulation",
                "execution_time_seconds": execution_time,
                "error": str(e)
            }

    def _extract_recommendations(self, analysis_text: str) -> List[str]:
        """Extract recommendations from analysis text."""
        # Simple extraction - in practice, this could use more sophisticated NLP
        recommendations = []
        lines = analysis_text.split('\n')

        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider']):
                if len(line) > 20 and not line.startswith('   '):  # Filter out sub-points
                    recommendations.append(line)

        return recommendations[:5]  # Limit to top 5 recommendations


class EcosystemWorkflowCoordinator:
    """Coordinator for ecosystem-wide workflow orchestration."""

    def __init__(self):
        """Initialize workflow coordinator."""
        self.logger = get_simulation_logger()
        self.orchestrator = SimulationWorkflowOrchestrator()

    async def coordinate_simulation_workflow(
        self, simulation_id: str, workflow_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Coordinate simulation workflow with ecosystem integration."""
        try:
            self.logger.info(
                "Coordinating simulation workflow",
                simulation_id=simulation_id,
                workflow_type=workflow_config.get("type", "unknown")
            )

            # Determine workflow type and execute
            workflow_type = workflow_config.get("type", "full_simulation")

            if workflow_type == "document_generation":
                result = await self.orchestrator.orchestrate_document_generation_workflow(
                    simulation_id, workflow_config.get("project_config", {})
                )
            elif workflow_type == "team_dynamics":
                result = await self.orchestrator.orchestrate_team_dynamics_workflow(
                    simulation_id, workflow_config.get("team_config", {})
                )
            elif workflow_type == "full_simulation":
                result = await self.orchestrator.orchestrate_full_simulation_workflow(
                    simulation_id, workflow_config
                )
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            return result

        except Exception as e:
            self.logger.error(
                "Workflow coordination failed",
                error=str(e),
                simulation_id=simulation_id,
                workflow_type=workflow_config.get("type", "unknown")
            )
            return {
                "success": False,
                "error": str(e),
                "simulation_id": simulation_id,
                "workflow_type": workflow_config.get("type", "unknown")
            }


# Global workflow coordinator instance
_workflow_coordinator: Optional[EcosystemWorkflowCoordinator] = None


def get_workflow_coordinator() -> EcosystemWorkflowCoordinator:
    """Get the global workflow coordinator instance."""
    global _workflow_coordinator
    if _workflow_coordinator is None:
        _workflow_coordinator = EcosystemWorkflowCoordinator()
    return _workflow_coordinator


__all__ = [
    'SimulationWorkflowOrchestrator',
    'EcosystemWorkflowCoordinator',
    'get_workflow_coordinator'
]
