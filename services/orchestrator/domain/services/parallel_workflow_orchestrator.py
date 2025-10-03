"""
Parallel Workflow Orchestrator - Phase 2 Day 5
Part of Enhanced Roadmap v2.0 - Final Integration

This orchestrator runs all 4 workflows (A, B, C, D) in parallel and aggregates results
into a comprehensive feature development roadmap.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

from services.orchestrator.domain.workflows import (
    # Workflow A
    FeatureDecompositionWorkflow,
    FeatureBreakdown,
    # Workflow B
    HistoricalContextWorkflow,
    HistoricalContext,
    # Workflow C
    TimelineAnalysisWorkflow,
    TimelineAnalysisResult,
    # Workflow D
    SkillsMatchingWorkflow,
    SkillsMatchingResult
)


@dataclass
class ComprehensiveRoadmap:
    """Complete roadmap generated from all 4 workflows."""
    orchestration_id: str
    query: str
    interpreted_query: Dict[str, Any]
    
    # Workflow A Results
    feature_breakdown: Optional[FeatureBreakdown] = None
    feature_breakdown_success: bool = False
    
    # Workflow B Results
    historical_context: Optional[HistoricalContext] = None
    historical_context_success: bool = False
    
    # Workflow C Results
    timeline_analysis: Optional[TimelineAnalysisResult] = None
    timeline_analysis_success: bool = False
    
    # Workflow D Results
    skills_matching: Optional[SkillsMatchingResult] = None
    skills_matching_success: bool = False
    
    # Aggregated Results
    overall_confidence: float = 0.0
    readiness_score: float = 0.0
    total_estimated_days: int = 0
    total_estimated_sprints: int = 0
    critical_risks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    workflows_completed: int = 0
    workflows_failed: int = 0
    total_processing_time_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def success_rate(self) -> float:
        """Calculate workflow success rate."""
        total = self.workflows_completed + self.workflows_failed
        return (self.workflows_completed / total) if total > 0 else 0.0


class ParallelWorkflowOrchestrator:
    """
    Orchestrates all 4 workflows in parallel for Enhanced Roadmap v2.0.
    
    Workflow Execution:
    - Workflow A: AI Feature Decomposition
    - Workflow B: Historical Context Retrieval
    - Workflow C: Timeline Analysis
    - Workflow D: Team Skills Matching
    
    All workflows run concurrently using async/await patterns.
    Results are aggregated into a comprehensive roadmap.
    
    Part of Enhanced Roadmap v2.0 Phase 2 final implementation.
    """
    
    def __init__(
        self,
        workflow_logger = None,
        # Service URLs
        llm_gateway_url: str = "http://llm-gateway:5000",
        prompt_store_url: str = "http://prompt-store:5110",
        analysis_service_url: str = "http://analysis-service:8004",
        memory_agent_url: str = "http://memory-agent:5090",
        doc_store_url: str = "http://doc-store:5140",
        source_agent_url: str = "http://source-agent:8001",
        project_simulation_url: str = "http://project-simulation:5075",
        user_store_url: str = "http://user-store:5130",
        project_planning_url: str = "http://project-planning-service:8000"
    ):
        """
        Initialize the parallel workflow orchestrator.
        
        Args:
            workflow_logger: WorkflowLogger instance for logging
            ..._url: Service URLs for workflow integrations
        """
        self.workflow_logger = workflow_logger
        
        # Initialize all 4 workflows
        self.workflow_a = FeatureDecompositionWorkflow(
            llm_gateway_url=llm_gateway_url,
            prompt_store_url=prompt_store_url,
            analysis_service_url=analysis_service_url,
            workflow_logger=workflow_logger
        )
        
        self.workflow_b = HistoricalContextWorkflow(
            memory_agent_url=memory_agent_url,
            doc_store_url=doc_store_url,
            source_agent_url=source_agent_url,
            workflow_logger=workflow_logger
        )
        
        self.workflow_c = TimelineAnalysisWorkflow(
            project_simulation_url=project_simulation_url,
            analysis_service_url=analysis_service_url,
            user_store_url=user_store_url,
            workflow_logger=workflow_logger
        )
        
        self.workflow_d = SkillsMatchingWorkflow(
            user_store_url=user_store_url,
            project_planning_url=project_planning_url,
            workflow_logger=workflow_logger
        )
    
    async def orchestrate(
        self,
        query: str,
        interpreted_query: Dict[str, Any],
        team_id: str = "default-team"
    ) -> ComprehensiveRoadmap:
        """
        Orchestrate all 4 workflows in parallel.
        
        Args:
            query: Original natural language query
            interpreted_query: Interpreted query from Interpreter service
            team_id: Team identifier for velocity/skills data
            
        Returns:
            ComprehensiveRoadmap with aggregated results from all workflows
        """
        orchestration_id = f"orch_{str(uuid.uuid4())[:8]}"
        start_time = datetime.utcnow()
        
        # Log orchestration start
        if self.workflow_logger:
            await self.workflow_logger.log_workflow_start(
                workflow_id=orchestration_id,
                operation="parallel_workflow_orchestration",
                context={
                    "query": query,
                    "team_id": team_id,
                    "workflows": ["A", "B", "C", "D"]
                }
            )
        
        try:
            # Execute all 4 workflows in parallel
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=orchestration_id,
                    step_name="parallel_execution_start",
                    step_data={"workflows_count": 4}
                )
            
            results = await asyncio.gather(
                self._execute_workflow_a(interpreted_query, orchestration_id),
                self._execute_workflow_b(interpreted_query, orchestration_id),
                # Workflow C depends on A's results, but we'll pass interpreted query
                self._execute_workflow_c_placeholder(interpreted_query, team_id, orchestration_id),
                self._execute_workflow_d_placeholder(interpreted_query, team_id, orchestration_id),
                return_exceptions=True  # Don't fail if one workflow fails
            )
            
            # Unpack results
            workflow_a_result, workflow_b_result, workflow_c_result, workflow_d_result = results
            
            # Log individual workflow completions
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=orchestration_id,
                    step_name="parallel_execution_complete",
                    step_data={
                        "workflow_a_success": not isinstance(workflow_a_result, Exception),
                        "workflow_b_success": not isinstance(workflow_b_result, Exception),
                        "workflow_c_success": not isinstance(workflow_c_result, Exception),
                        "workflow_d_success": not isinstance(workflow_d_result, Exception)
                    }
                )
            
            # Now execute C and D with actual A results (if available)
            if not isinstance(workflow_a_result, Exception):
                # Re-run C and D with Workflow A's actual results
                workflow_c_result, workflow_d_result = await asyncio.gather(
                    self._execute_workflow_c(workflow_a_result, team_id, orchestration_id),
                    self._execute_workflow_d(workflow_a_result, team_id, orchestration_id),
                    return_exceptions=True
                )
            
            # Create comprehensive roadmap
            roadmap = ComprehensiveRoadmap(
                orchestration_id=orchestration_id,
                query=query,
                interpreted_query=interpreted_query
            )
            
            # Populate workflow A results
            if not isinstance(workflow_a_result, Exception):
                roadmap.feature_breakdown = workflow_a_result
                roadmap.feature_breakdown_success = True
                roadmap.workflows_completed += 1
            else:
                roadmap.workflows_failed += 1
            
            # Populate workflow B results
            if not isinstance(workflow_b_result, Exception):
                roadmap.historical_context = workflow_b_result
                roadmap.historical_context_success = True
                roadmap.workflows_completed += 1
            else:
                roadmap.workflows_failed += 1
            
            # Populate workflow C results
            if not isinstance(workflow_c_result, Exception):
                roadmap.timeline_analysis = workflow_c_result
                roadmap.timeline_analysis_success = True
                roadmap.workflows_completed += 1
            else:
                roadmap.workflows_failed += 1
            
            # Populate workflow D results
            if not isinstance(workflow_d_result, Exception):
                roadmap.skills_matching = workflow_d_result
                roadmap.skills_matching_success = True
                roadmap.workflows_completed += 1
            else:
                roadmap.workflows_failed += 1
            
            # Aggregate results
            await self._aggregate_results(roadmap)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            roadmap.total_processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log orchestration completion
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_complete(
                    workflow_id=orchestration_id,
                    duration_ms=roadmap.total_processing_time_ms,
                    success=True,
                    result_summary={
                        "workflows_completed": roadmap.workflows_completed,
                        "workflows_failed": roadmap.workflows_failed,
                        "success_rate": roadmap.success_rate,
                        "overall_confidence": roadmap.overall_confidence,
                        "readiness_score": roadmap.readiness_score
                    }
                )
            
            return roadmap
            
        except Exception as e:
            # Log error
            if self.workflow_logger:
                await self.workflow_logger.log_error(
                    workflow_id=orchestration_id,
                    error=e,
                    context={"stage": "parallel_workflow_orchestration"}
                )
            raise
    
    async def _execute_workflow_a(
        self,
        interpreted_query: Dict[str, Any],
        parent_workflow_id: str
    ) -> FeatureBreakdown:
        """Execute Workflow A: Feature Decomposition."""
        feature_title = interpreted_query.get("entities", {}).get("feature_title", "New Feature")
        feature_description = interpreted_query.get("query", "")
        context = interpreted_query.get("entities", {})
        
        return await self.workflow_a.execute(
            feature_description=feature_description,
            feature_title=feature_title,
            context=context,
            parent_workflow_id=parent_workflow_id
        )
    
    async def _execute_workflow_b(
        self,
        interpreted_query: Dict[str, Any],
        parent_workflow_id: str
    ) -> HistoricalContext:
        """Execute Workflow B: Historical Context Retrieval."""
        query_context = interpreted_query.get("entities", {})
        
        return await self.workflow_b.execute(
            query_context=query_context,
            parent_workflow_id=parent_workflow_id,
            max_sources=50
        )
    
    async def _execute_workflow_c_placeholder(
        self,
        interpreted_query: Dict[str, Any],
        team_id: str,
        parent_workflow_id: str
    ) -> TimelineAnalysisResult:
        """Execute Workflow C placeholder (will re-run with A's results)."""
        # Placeholder - will be re-run with actual feature breakdown
        feature_breakdown = {
            "feature_id": "placeholder",
            "total_story_points": 30,
            "user_stories": [],
            "technical_tasks": []
        }
        
        return await self.workflow_c.execute(
            feature_breakdown=feature_breakdown,
            team_id=team_id,
            parent_workflow_id=parent_workflow_id
        )
    
    async def _execute_workflow_c(
        self,
        feature_breakdown: FeatureBreakdown,
        team_id: str,
        parent_workflow_id: str
    ) -> TimelineAnalysisResult:
        """Execute Workflow C: Timeline Analysis with actual feature breakdown."""
        # Convert FeatureBreakdown to dict
        feature_breakdown_dict = {
            "feature_id": feature_breakdown.feature_id,
            "feature_title": feature_breakdown.feature_title,
            "total_story_points": feature_breakdown.total_story_points,
            "user_stories": [
                {
                    "id": story.id,
                    "title": story.title,
                    "story_points": story.story_points
                }
                for story in feature_breakdown.user_stories
            ],
            "technical_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "estimated_hours": task.estimated_hours,
                    "complexity": task.complexity,
                    "required_skills": task.required_skills
                }
                for task in feature_breakdown.technical_tasks
            ]
        }
        
        return await self.workflow_c.execute(
            feature_breakdown=feature_breakdown_dict,
            team_id=team_id,
            parent_workflow_id=parent_workflow_id
        )
    
    async def _execute_workflow_d_placeholder(
        self,
        interpreted_query: Dict[str, Any],
        team_id: str,
        parent_workflow_id: str
    ) -> SkillsMatchingResult:
        """Execute Workflow D placeholder (will re-run with A's results)."""
        # Placeholder - will be re-run with actual feature breakdown
        feature_breakdown = {
            "feature_id": "placeholder",
            "technical_tasks": []
        }
        
        return await self.workflow_d.execute(
            feature_breakdown=feature_breakdown,
            team_id=team_id,
            parent_workflow_id=parent_workflow_id
        )
    
    async def _execute_workflow_d(
        self,
        feature_breakdown: FeatureBreakdown,
        team_id: str,
        parent_workflow_id: str
    ) -> SkillsMatchingResult:
        """Execute Workflow D: Skills Matching with actual feature breakdown."""
        # Convert FeatureBreakdown to dict
        feature_breakdown_dict = {
            "feature_id": feature_breakdown.feature_id,
            "technical_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "estimated_hours": task.estimated_hours,
                    "complexity": task.complexity,
                    "required_skills": task.required_skills
                }
                for task in feature_breakdown.technical_tasks
            ]
        }
        
        return await self.workflow_d.execute(
            feature_breakdown=feature_breakdown_dict,
            team_id=team_id,
            parent_workflow_id=parent_workflow_id
        )
    
    async def _aggregate_results(self, roadmap: ComprehensiveRoadmap):
        """Aggregate results from all workflows into roadmap."""
        # Calculate overall confidence
        confidences = []
        if roadmap.feature_breakdown:
            confidences.append(roadmap.feature_breakdown.complexity_score)
        if roadmap.historical_context:
            confidences.append(roadmap.historical_context.average_relevance)
        if roadmap.timeline_analysis:
            confidences.append(roadmap.timeline_analysis.overall_confidence)
        if roadmap.skills_matching:
            confidences.append(roadmap.skills_matching.overall_readiness)
        
        roadmap.overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Calculate readiness score (from Workflow D)
        if roadmap.skills_matching:
            roadmap.readiness_score = roadmap.skills_matching.overall_readiness
        
        # Extract timeline estimates (from Workflow C)
        if roadmap.timeline_analysis and roadmap.timeline_analysis.timeline_estimates:
            roadmap.total_estimated_days = sum(
                e.estimated_duration_days for e in roadmap.timeline_analysis.timeline_estimates
            )
            roadmap.total_estimated_sprints = sum(
                e.estimated_sprints for e in roadmap.timeline_analysis.timeline_estimates
            )
        
        # Aggregate critical risks
        if roadmap.feature_breakdown:
            roadmap.critical_risks.extend([
                f for f in roadmap.feature_breakdown.risk_factors
                if "critical" in f.lower() or "high" in f.lower()
            ])
        
        if roadmap.timeline_analysis:
            roadmap.critical_risks.extend(roadmap.timeline_analysis.risk_factors[:3])  # Top 3
        
        if roadmap.skills_matching:
            critical_gaps = [
                f"Critical skill gap: {gap.skill_name}"
                for gap in roadmap.skills_matching.skill_gaps
                if gap.gap_severity == "critical"
            ]
            roadmap.critical_risks.extend(critical_gaps)
        
        # Aggregate recommendations
        if roadmap.feature_breakdown and hasattr(roadmap.feature_breakdown, 'recommendations'):
            roadmap.recommendations.extend(roadmap.feature_breakdown.recommendations[:2])
        
        if roadmap.timeline_analysis:
            roadmap.recommendations.extend(roadmap.timeline_analysis.recommendations[:3])
        
        if roadmap.skills_matching:
            roadmap.recommendations.extend(roadmap.skills_matching.recommendations[:2])

