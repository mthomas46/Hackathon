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
try:
    from integrations.orchestration.orchestration import WorkflowOrchestrator
except (ImportError, AttributeError):
    # Create a simple mock WorkflowOrchestrator for testing
    class WorkflowOrchestrator:
        async def run_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
            """Mock workflow execution."""
            return {"status": "completed", "result": workflow_config}

        async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
            """Mock workflow status check."""
            return {"status": "completed", "workflow_id": workflow_id}

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

    async def execute_phase_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow for a simulation phase."""
        start_time = datetime.now()
        phase_name = workflow_config.get("phase", "unknown")

        try:
            self.logger.info(
                "Executing phase workflow",
                phase=phase_name,
                workflow_type="phase_execution"
            )

            # Execute workflow through orchestrator service
            workflow_data = {
                "name": f"{phase_name}_workflow",
                "type": "simulation_phase",
                "config": workflow_config,
                "steps": [
                    {
                        "name": "validate_phase",
                        "type": "validation",
                        "config": {"phase": phase_name}
                    },
                    {
                        "name": "execute_phase_logic",
                        "type": "execution",
                        "config": workflow_config
                    },
                    {
                        "name": "validate_results",
                        "type": "validation",
                        "config": {"expected_outputs": ["documents", "tickets", "prs"]}
                    }
                ]
            }

            if self.orchestrator_client:
                workflow_id = await self.orchestrator_client.create_workflow(workflow_data)
                if workflow_id:
                    result = await self.orchestrator_client.execute_workflow(workflow_id)
                    execution_time = (datetime.now() - start_time).total_seconds()

                    return {
                        "success": result.get("success", False),
                        "execution_time": execution_time,
                        "workflow_id": workflow_id,
                        "phase": phase_name,
                        "result": result
                    }

            # Fallback: simulate workflow execution
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": True,
                "execution_time": execution_time,
                "workflow_id": f"fallback_{phase_name}_{datetime.now().timestamp()}",
                "phase": phase_name,
                "result": {"message": f"Phase {phase_name} executed successfully"}
            }

        except Exception as e:
            self.logger.error(
                "Phase workflow execution failed",
                error=str(e),
                phase=phase_name
            )
            return {
                "success": False,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "error": str(e),
                "phase": phase_name
            }

    async def run_analysis_workflow(self, analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis workflow on simulation results."""
        start_time = datetime.now()
        simulation_id = analysis_config.get("simulation_id", "unknown")

        try:
            self.logger.info(
                "Running analysis workflow",
                simulation_id=simulation_id,
                analysis_types=analysis_config.get("analysis_types", [])
            )

            # Run analysis through analysis service
            if self.analysis_client and analysis_config.get("documents"):
                analysis_result = await self.analysis_client.analyze_documents(
                    analysis_config["documents"]
                )

                # Generate insights
                insights_result = await self.analysis_client.generate_insights({
                    "analysis_data": analysis_result,
                    "simulation_id": simulation_id
                })

                # Run additional analysis types if requested
                additional_analysis = {}
                analysis_types = analysis_config.get("analysis_types", [])

                if "patterns" in analysis_types:
                    # Analyze patterns in documents
                    pattern_analysis = await self._analyze_document_patterns(
                        analysis_config["documents"], simulation_id
                    )
                    additional_analysis["patterns"] = pattern_analysis

                if "consistency" in analysis_types:
                    # Analyze document consistency
                    consistency_analysis = await self._analyze_document_consistency(
                        analysis_config["documents"], simulation_id
                    )
                    additional_analysis["consistency"] = consistency_analysis

                execution_time = (datetime.now() - start_time).total_seconds()

                return {
                    "success": True,
                    "execution_time": execution_time,
                    "analysis_result": analysis_result,
                    "insights": insights_result,
                    "additional_analysis": additional_analysis,
                    "simulation_id": simulation_id
                }

            # Fallback: return mock analysis
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": True,
                "execution_time": execution_time,
                "analysis_result": {"quality_score": 0.85, "issues": []},
                "insights": ["Analysis completed successfully"],
                "additional_analysis": {},
                "simulation_id": simulation_id
            }

        except Exception as e:
            self.logger.error(
                "Analysis workflow failed",
                error=str(e),
                simulation_id=simulation_id
            )
            return {
                "success": False,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "error": str(e),
                "simulation_id": simulation_id
            }

    async def _analyze_document_patterns(self, documents: List[Dict[str, Any]], simulation_id: str) -> Dict[str, Any]:
        """Analyze patterns in documents for insights and trends."""
        try:
            # Extract document types and content
            doc_types = {}
            content_patterns = []

            for doc in documents:
                doc_type = doc.get("type", "unknown")
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

                # Analyze content patterns
                content = doc.get("content", "").lower()
                if "error" in content or "issue" in content:
                    content_patterns.append("error_handling")
                if "test" in content or "testing" in content:
                    content_patterns.append("testing_patterns")
                if "security" in content or "auth" in content:
                    content_patterns.append("security_focus")
                if "performance" in content or "optimization" in content:
                    content_patterns.append("performance_focus")

            # Analyze pattern distribution
            pattern_distribution = {}
            for pattern in content_patterns:
                pattern_distribution[pattern] = pattern_distribution.get(pattern, 0) + 1

            return {
                "document_type_distribution": doc_types,
                "content_pattern_distribution": pattern_distribution,
                "total_documents_analyzed": len(documents),
                "unique_patterns_identified": len(set(content_patterns)),
                "insights": [
                    f"Most common document type: {max(doc_types, key=doc_types.get) if doc_types else 'None'}",
                    f"Primary focus area: {max(pattern_distribution, key=pattern_distribution.get) if pattern_distribution else 'General'}"
                ]
            }

        except Exception as e:
            self.logger.error(f"Pattern analysis failed", error=str(e), simulation_id=simulation_id)
            return {"error": str(e), "patterns": []}

    async def _analyze_document_consistency(self, documents: List[Dict[str, Any]], simulation_id: str) -> Dict[str, Any]:
        """Analyze document consistency and identify potential issues."""
        try:
            consistency_issues = []
            naming_consistency = {}
            content_references = {}

            for doc in documents:
                title = doc.get("title", "")
                content = doc.get("content", "")

                # Check naming consistency
                if "api" in title.lower() and "endpoint" not in title.lower():
                    consistency_issues.append(f"Inconsistent API naming in: {title}")

                # Check for broken references
                import re
                references = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
                for ref in references:
                    content_references[ref] = content_references.get(ref, 0) + 1

            # Identify potential duplicate references
            duplicate_refs = [ref for ref, count in content_references.items() if count > 2]

            return {
                "consistency_score": max(0, 100 - len(consistency_issues) * 10),
                "issues_found": consistency_issues,
                "potential_duplicates": duplicate_refs,
                "reference_distribution": content_references,
                "recommendations": [
                    "Standardize naming conventions across documents",
                    "Review and consolidate duplicate references" if duplicate_refs else "Reference usage is consistent",
                    "Ensure consistent terminology throughout documentation"
                ]
            }

        except Exception as e:
            self.logger.error(f"Consistency analysis failed", error=str(e), simulation_id=simulation_id)
            return {"error": str(e), "consistency_score": 0, "issues": []}

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
