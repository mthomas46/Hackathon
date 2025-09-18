"""Analytics Integration - Comprehensive Analysis Service Integration.

This module implements sophisticated analytics integration that leverages existing
analysis_service patterns to provide comprehensive project analysis, insights, and
intelligent recommendations for the Project Simulation Service.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime, timedelta
from enum import Enum
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.content.context_aware_generation import ContentContext
from simulation.infrastructure.integration.service_clients import get_ecosystem_client


class AnalysisType(Enum):
    """Types of analysis that can be performed."""
    DOCUMENT_QUALITY = "document_quality"
    CODE_COMPLEXITY = "code_complexity"
    TEAM_PRODUCTIVITY = "team_productivity"
    PROJECT_RISKS = "project_risks"
    REQUIREMENT_COVERAGE = "requirement_coverage"
    TEST_COVERAGE = "test_coverage"
    ARCHITECTURE_COMPLIANCE = "architecture_compliance"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_METRICS = "performance_metrics"
    COST_ANALYSIS = "cost_analysis"


class InsightPriority(Enum):
    """Priority levels for insights."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class InsightCategory(Enum):
    """Categories for insights."""
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    RISK = "risk"
    COMPLIANCE = "compliance"
    INNOVATION = "innovation"
    PRODUCTIVITY = "productivity"


class AnalysisInsight:
    """Represents an insight from analysis."""

    def __init__(self,
                 insight_id: str,
                 analysis_type: AnalysisType,
                 category: InsightCategory,
                 priority: InsightPriority,
                 title: str,
                 description: str,
                 confidence_score: float,
                 impact_score: float,
                 recommendations: List[str],
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize analysis insight."""
        self.insight_id = insight_id
        self.analysis_type = analysis_type
        self.category = category
        self.priority = priority
        self.title = title
        self.description = description
        self.confidence_score = confidence_score
        self.impact_score = impact_score
        self.recommendations = recommendations
        self.metadata = metadata or {}
        self.generated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "insight_id": self.insight_id,
            "analysis_type": self.analysis_type.value,
            "category": self.category.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "confidence_score": self.confidence_score,
            "impact_score": self.impact_score,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat()
        }


class AnalysisWorkflow:
    """Represents a reusable analysis workflow."""

    def __init__(self,
                 workflow_id: str,
                 name: str,
                 description: str,
                 analysis_types: List[AnalysisType],
                 input_requirements: Dict[str, Any],
                 output_format: Dict[str, Any]):
        """Initialize analysis workflow."""
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.analysis_types = analysis_types
        self.input_requirements = input_requirements
        self.output_format = output_format

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "analysis_types": [t.value for t in self.analysis_types],
            "input_requirements": self.input_requirements,
            "output_format": self.output_format
        }


class AnalyticsIntegrationManager:
    """Manages integration with analysis_service and other analytics components."""

    def __init__(self):
        """Initialize analytics integration manager."""
        self.logger = get_simulation_logger()

        # Service clients
        self.analysis_client = get_ecosystem_client("analysis_service")
        self.interpreter_client = get_ecosystem_client("interpreter")
        self.doc_store_client = get_ecosystem_client("doc_store")

        # Analysis workflows
        self.workflows = self._load_analysis_workflows()

        # Insight storage
        self.insights: List[AnalysisInsight] = []

        # Analysis cache
        self.analysis_cache: Dict[str, Any] = {}

    def _load_analysis_workflows(self) -> Dict[str, AnalysisWorkflow]:
        """Load predefined analysis workflows."""
        workflows = {}

        # Document Quality Analysis Workflow
        workflows["document_quality"] = AnalysisWorkflow(
            workflow_id="document_quality",
            name="Document Quality Analysis",
            description="Comprehensive analysis of document quality, completeness, and compliance",
            analysis_types=[AnalysisType.DOCUMENT_QUALITY, AnalysisType.REQUIREMENT_COVERAGE],
            input_requirements={
                "documents": "List of document IDs to analyze",
                "quality_criteria": "Quality assessment criteria",
                "compliance_standards": "Applicable compliance standards"
            },
            output_format={
                "quality_score": "Overall quality score (0-1)",
                "issues": "List of identified issues",
                "recommendations": "Suggested improvements",
                "compliance_status": "Compliance assessment"
            }
        )

        # Project Risk Analysis Workflow
        workflows["project_risks"] = AnalysisWorkflow(
            workflow_id="project_risks",
            name="Project Risk Assessment",
            description="Comprehensive risk analysis for project success factors",
            analysis_types=[AnalysisType.PROJECT_RISKS, AnalysisType.TEAM_PRODUCTIVITY, AnalysisType.COST_ANALYSIS],
            input_requirements={
                "project_config": "Project configuration and requirements",
                "team_data": "Team composition and performance data",
                "timeline_data": "Project timeline and milestones",
                "budget_data": "Budget and cost information"
            },
            output_format={
                "risk_score": "Overall project risk score (0-1)",
                "risk_factors": "Identified risk factors",
                "mitigation_strategies": "Recommended risk mitigation approaches",
                "confidence_intervals": "Risk probability ranges"
            }
        )

        # Team Performance Analysis Workflow
        workflows["team_performance"] = AnalysisWorkflow(
            workflow_id="team_performance",
            name="Team Performance Analytics",
            description="Analysis of team productivity, collaboration, and performance metrics",
            analysis_types=[AnalysisType.TEAM_PRODUCTIVITY, AnalysisType.CODE_COMPLEXITY, AnalysisType.TEST_COVERAGE],
            input_requirements={
                "team_members": "Team member data and roles",
                "performance_metrics": "Individual and team performance data",
                "collaboration_data": "Team collaboration patterns",
                "workload_data": "Current and planned workload"
            },
            output_format={
                "productivity_score": "Team productivity score (0-1)",
                "bottlenecks": "Identified performance bottlenecks",
                "optimization_opportunities": "Performance improvement recommendations",
                "resource_allocation": "Optimal resource allocation suggestions"
            }
        )

        # Architecture Compliance Analysis Workflow
        workflows["architecture_compliance"] = AnalysisWorkflow(
            workflow_id="architecture_compliance",
            name="Architecture Compliance Analysis",
            description="Analysis of architectural compliance and design quality",
            analysis_types=[AnalysisType.ARCHITECTURE_COMPLIANCE, AnalysisType.SECURITY_ANALYSIS],
            input_requirements={
                "architecture_docs": "Architecture documentation",
                "design_documents": "Detailed design specifications",
                "implementation_artifacts": "Code and implementation artifacts",
                "standards": "Applicable architectural standards"
            },
            output_format={
                "compliance_score": "Architecture compliance score (0-1)",
                "violations": "Identified architectural violations",
                "recommendations": "Architecture improvement recommendations",
                "standards_alignment": "Standards compliance assessment"
            }
        )

        return workflows

    async def execute_analysis_workflow(self,
                                      workflow_id: str,
                                      context: ContentContext,
                                      **kwargs) -> Dict[str, Any]:
        """Execute a complete analysis workflow."""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"Analysis workflow {workflow_id} not found")

            workflow = self.workflows[workflow_id]
            self.logger.info("Executing analysis workflow",
                           workflow_id=workflow_id, name=workflow.name)

            # Prepare analysis inputs
            analysis_inputs = self._prepare_workflow_inputs(workflow, context, **kwargs)

            # Execute analysis components
            analysis_results = {}
            insights = []

            for analysis_type in workflow.analysis_types:
                try:
                    result = await self._execute_analysis_component(analysis_type, analysis_inputs, context)
                    analysis_results[analysis_type.value] = result

                    # Generate insights from results
                    component_insights = self._generate_insights_from_analysis(
                        analysis_type, result, context
                    )
                    insights.extend(component_insights)

                except Exception as e:
                    self.logger.warning("Analysis component failed",
                                      component=analysis_type.value, error=str(e))
                    analysis_results[analysis_type.value] = {"error": str(e)}

            # Aggregate results
            aggregated_results = self._aggregate_workflow_results(workflow, analysis_results, insights)

            # Store insights
            self.insights.extend(insights)

            # Cache results
            cache_key = f"{workflow_id}_{context.project_config.get('id', 'unknown')}_{datetime.now().date()}"
            self.analysis_cache[cache_key] = {
                "results": aggregated_results,
                "insights": [insight.to_dict() for insight in insights],
                "timestamp": datetime.now()
            }

            return aggregated_results

        except Exception as e:
            self.logger.error("Analysis workflow execution failed",
                            workflow_id=workflow_id, error=str(e))
            raise

    def _prepare_workflow_inputs(self,
                               workflow: AnalysisWorkflow,
                               context: ContentContext,
                               **kwargs) -> Dict[str, Any]:
        """Prepare inputs for workflow execution."""
        inputs = {}

        # Extract relevant data from context
        if "documents" in workflow.input_requirements:
            inputs["documents"] = self._extract_document_data(context, **kwargs)

        if "project_config" in workflow.input_requirements:
            inputs["project_config"] = context.project_config

        if "team_data" in workflow.input_requirements:
            inputs["team_data"] = {
                "members": list(context.team_profiles.values()),
                "dynamics": context.team_dynamics,
                "size": context.team_dynamics["team_size"]
            }

        if "timeline_data" in workflow.input_requirements:
            inputs["timeline_data"] = {
                "phases": context.timeline.get("phases", []),
                "intelligence": context.timeline_awareness
            }

        # Add any additional inputs from kwargs
        inputs.update(kwargs)

        return inputs

    async def _execute_analysis_component(self,
                                       analysis_type: AnalysisType,
                                       inputs: Dict[str, Any],
                                       context: ContentContext) -> Dict[str, Any]:
        """Execute a specific analysis component."""
        try:
            if analysis_type == AnalysisType.DOCUMENT_QUALITY:
                return await self._analyze_document_quality(inputs, context)

            elif analysis_type == AnalysisType.PROJECT_RISKS:
                return await self._analyze_project_risks(inputs, context)

            elif analysis_type == AnalysisType.TEAM_PRODUCTIVITY:
                return await self._analyze_team_productivity(inputs, context)

            elif analysis_type == AnalysisType.REQUIREMENT_COVERAGE:
                return await self._analyze_requirement_coverage(inputs, context)

            elif analysis_type == AnalysisType.TEST_COVERAGE:
                return await self._analyze_test_coverage(inputs, context)

            elif analysis_type == AnalysisType.ARCHITECTURE_COMPLIANCE:
                return await self._analyze_architecture_compliance(inputs, context)

            else:
                return {"status": "not_implemented", "message": f"Analysis type {analysis_type.value} not implemented"}

        except Exception as e:
            self.logger.error("Analysis component execution failed",
                            component=analysis_type.value, error=str(e))
            return {"status": "error", "error": str(e)}

    async def _analyze_document_quality(self, inputs: Dict[str, Any], context: ContentContext) -> Dict[str, Any]:
        """Analyze document quality using analysis_service patterns."""
        documents = inputs.get("documents", [])

        if not documents:
            return {"quality_score": 0.0, "issues": ["No documents provided for analysis"]}

        try:
            # Use analysis_service for document quality analysis
            quality_analysis = await self.analysis_client.analyze_document_quality(
                document_ids=documents,
                criteria=inputs.get("quality_criteria", ["completeness", "clarity", "consistency"])
            )

            return {
                "quality_score": quality_analysis.get("overall_score", 0.5),
                "issues": quality_analysis.get("issues", []),
                "strengths": quality_analysis.get("strengths", []),
                "recommendations": quality_analysis.get("recommendations", [])
            }

        except Exception as e:
            self.logger.warning("Document quality analysis failed, using fallback", error=str(e))
            return self._fallback_document_quality_analysis(documents)

    async def _analyze_project_risks(self, inputs: Dict[str, Any], context: ContentContext) -> Dict[str, Any]:
        """Analyze project risks comprehensively."""
        project_config = inputs.get("project_config", {})
        team_data = inputs.get("team_data", {})
        timeline_data = inputs.get("timeline_data", {})

        risk_factors = []

        # Timeline-based risks
        timeline_risks = self._assess_timeline_risks(timeline_data)
        risk_factors.extend(timeline_risks)

        # Team-based risks
        team_risks = self._assess_team_risks(team_data)
        risk_factors.extend(team_risks)

        # Complexity-based risks
        complexity_risks = self._assess_complexity_risks(project_config)
        risk_factors.extend(complexity_risks)

        # Calculate overall risk score
        risk_score = self._calculate_risk_score(risk_factors)

        return {
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "risk_distribution": self._categorize_risks(risk_factors),
            "mitigation_strategies": self._generate_risk_mitigation(risk_factors)
        }

    async def _analyze_team_productivity(self, inputs: Dict[str, Any], context: ContentContext) -> Dict[str, Any]:
        """Analyze team productivity using existing patterns."""
        team_data = inputs.get("team_data", {})

        # Calculate productivity metrics
        productivity_metrics = self._calculate_productivity_metrics(team_data)

        # Identify bottlenecks
        bottlenecks = self._identify_productivity_bottlenecks(team_data, productivity_metrics)

        # Generate optimization recommendations
        recommendations = self._generate_productivity_recommendations(bottlenecks, team_data)

        return {
            "productivity_score": productivity_metrics["overall_score"],
            "metrics": productivity_metrics,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "optimization_opportunities": self._identify_optimization_opportunities(team_data)
        }

    def _generate_insights_from_analysis(self,
                                       analysis_type: AnalysisType,
                                       results: Dict[str, Any],
                                       context: ContentContext) -> List[AnalysisInsight]:
        """Generate insights from analysis results."""
        insights = []

        if analysis_type == AnalysisType.DOCUMENT_QUALITY:
            insights.extend(self._generate_document_quality_insights(results, context))

        elif analysis_type == AnalysisType.PROJECT_RISKS:
            insights.extend(self._generate_risk_insights(results, context))

        elif analysis_type == AnalysisType.TEAM_PRODUCTIVITY:
            insights.extend(self._generate_productivity_insights(results, context))

        return insights

    def _generate_document_quality_insights(self, results: Dict[str, Any], context: ContentContext) -> List[AnalysisInsight]:
        """Generate insights from document quality analysis."""
        insights = []

        quality_score = results.get("quality_score", 0.5)

        if quality_score < 0.6:
            insights.append(AnalysisInsight(
                insight_id=f"doc_quality_{datetime.now().timestamp()}",
                analysis_type=AnalysisType.DOCUMENT_QUALITY,
                category=InsightCategory.QUALITY,
                priority=InsightPriority.HIGH,
                title="Document Quality Issues Detected",
                description=f"Document quality score of {quality_score:.2f} indicates significant improvement opportunities",
                confidence_score=0.85,
                impact_score=0.7,
                recommendations=results.get("recommendations", []),
                metadata={"quality_score": quality_score, "issues_count": len(results.get("issues", []))}
            ))

        return insights

    def _generate_risk_insights(self, results: Dict[str, Any], context: ContentContext) -> List[AnalysisInsight]:
        """Generate insights from risk analysis."""
        insights = []

        risk_score = results.get("risk_score", 0.5)

        if risk_score > 0.7:
            insights.append(AnalysisInsight(
                insight_id=f"risk_{datetime.now().timestamp()}",
                analysis_type=AnalysisType.PROJECT_RISKS,
                category=InsightCategory.RISK,
                priority=InsightPriority.CRITICAL,
                title="High Project Risk Detected",
                description=f"Project risk score of {risk_score:.2f} requires immediate attention",
                confidence_score=0.9,
                impact_score=0.9,
                recommendations=results.get("mitigation_strategies", []),
                metadata={"risk_score": risk_score, "risk_factors": len(results.get("risk_factors", []))}
            ))

        return insights

    def _generate_productivity_insights(self, results: Dict[str, Any], context: ContentContext) -> List[AnalysisInsight]:
        """Generate insights from productivity analysis."""
        insights = []

        productivity_score = results.get("productivity_score", 0.5)

        if productivity_score < 0.6:
            insights.append(AnalysisInsight(
                insight_id=f"productivity_{datetime.now().timestamp()}",
                analysis_type=AnalysisType.TEAM_PRODUCTIVITY,
                category=InsightCategory.PRODUCTIVITY,
                priority=InsightPriority.MEDIUM,
                title="Team Productivity Optimization Needed",
                description=f"Team productivity score of {productivity_score:.2f} suggests optimization opportunities",
                confidence_score=0.8,
                impact_score=0.6,
                recommendations=results.get("recommendations", []),
                metadata={"productivity_score": productivity_score, "bottlenecks": len(results.get("bottlenecks", []))}
            ))

        return insights

    def _aggregate_workflow_results(self,
                                  workflow: AnalysisWorkflow,
                                  analysis_results: Dict[str, Any],
                                  insights: List[AnalysisInsight]) -> Dict[str, Any]:
        """Aggregate results from all analysis components."""
        # Calculate overall scores
        overall_score = 0.0
        component_count = 0

        for result in analysis_results.values():
            if isinstance(result, dict) and "status" not in result:
                # Try to extract score from result
                score = result.get("quality_score") or result.get("risk_score") or result.get("productivity_score") or 0.5
                overall_score += score
                component_count += 1

        overall_score = overall_score / max(1, component_count)

        return {
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.name,
            "overall_score": overall_score,
            "component_results": analysis_results,
            "insights_count": len(insights),
            "insights": [insight.to_dict() for insight in insights],
            "generated_at": datetime.now(),
            "recommendations": self._aggregate_recommendations(insights)
        }

    def _aggregate_recommendations(self, insights: List[AnalysisInsight]) -> List[str]:
        """Aggregate recommendations from all insights."""
        all_recommendations = []

        for insight in insights:
            all_recommendations.extend(insight.recommendations)

        # Remove duplicates and prioritize by insight priority
        unique_recommendations = list(set(all_recommendations))

        # Sort by priority (critical first)
        priority_order = {InsightPriority.CRITICAL: 0, InsightPriority.HIGH: 1,
                         InsightPriority.MEDIUM: 2, InsightPriority.LOW: 3, InsightPriority.INFO: 4}

        sorted_insights = sorted(insights, key=lambda i: priority_order[i.priority])

        prioritized_recommendations = []
        for insight in sorted_insights:
            prioritized_recommendations.extend(insight.recommendations)

        return list(dict.fromkeys(prioritized_recommendations))  # Remove duplicates while preserving order

    # Helper methods for analysis components
    def _assess_timeline_risks(self, timeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess timeline-based risks."""
        risks = []

        progress = timeline_data.get("intelligence", {}).get("progress_percentage", 0)
        time_pressure = timeline_data.get("intelligence", {}).get("time_pressure", 1.0)

        if progress < 30 and time_pressure > 1.5:
            risks.append({
                "type": "timeline_delay",
                "severity": "high",
                "description": "Significant time pressure with low progress",
                "probability": 0.8,
                "impact": "high"
            })

        return risks

    def _assess_team_risks(self, team_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess team-based risks."""
        risks = []

        team_size = team_data.get("size", 0)

        if team_size < 3:
            risks.append({
                "type": "small_team",
                "severity": "medium",
                "description": "Small team size may limit capacity",
                "probability": 0.6,
                "impact": "medium"
            })

        return risks

    def _assess_complexity_risks(self, project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess complexity-based risks."""
        risks = []

        complexity = project_config.get("complexity", "medium")

        if complexity == "complex":
            risks.append({
                "type": "high_complexity",
                "severity": "high",
                "description": "High project complexity increases risk",
                "probability": 0.7,
                "impact": "high"
            })

        return risks

    def _calculate_risk_score(self, risk_factors: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score."""
        if not risk_factors:
            return 0.2

        total_weighted_risk = 0.0
        total_weight = 0.0

        severity_weights = {"low": 0.3, "medium": 0.6, "high": 1.0}
        impact_weights = {"low": 0.3, "medium": 0.6, "high": 1.0}

        for risk in risk_factors:
            severity_weight = severity_weights.get(risk.get("severity", "medium"), 0.6)
            impact_weight = impact_weights.get(risk.get("impact", "medium"), 0.6)
            probability = risk.get("probability", 0.5)

            weighted_risk = severity_weight * impact_weight * probability
            total_weighted_risk += weighted_risk
            total_weight += 1.0

        return min(1.0, total_weighted_risk / max(1.0, total_weight))

    def _fallback_document_quality_analysis(self, documents: List[str]) -> Dict[str, Any]:
        """Fallback document quality analysis when service is unavailable."""
        return {
            "quality_score": 0.5,
            "issues": ["Analysis service unavailable - using basic assessment"],
            "recommendations": ["Verify analysis service connectivity", "Review documents manually"]
        }

    def _extract_document_data(self, context: ContentContext, **kwargs) -> List[str]:
        """Extract document data from context."""
        # This would integrate with doc_store to get actual document IDs
        # For now, return mock document IDs
        return [f"doc_{i}" for i in range(len(context.project_config.get("documents", [])))]

    def _calculate_productivity_metrics(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate team productivity metrics."""
        return {"overall_score": 0.75, "individual_scores": {}, "team_efficiency": 0.8}

    def _identify_productivity_bottlenecks(self, team_data: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
        """Identify productivity bottlenecks."""
        return ["Resource allocation", "Communication overhead"]

    def _generate_productivity_recommendations(self, bottlenecks: List[str], team_data: Dict[str, Any]) -> List[str]:
        """Generate productivity recommendations."""
        return ["Optimize resource allocation", "Improve communication channels"]

    def _identify_optimization_opportunities(self, team_data: Dict[str, Any]) -> List[str]:
        """Identify optimization opportunities."""
        return ["Process automation", "Skill development"]

    def _categorize_risks(self, risk_factors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize risks by type."""
        categories = {}
        for risk in risk_factors:
            category = risk.get("type", "unknown")
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _generate_risk_mitigation(self, risk_factors: List[Dict[str, Any]]) -> List[str]:
        """Generate risk mitigation strategies."""
        return ["Implement risk monitoring", "Develop contingency plans", "Increase resource allocation"]


# Global analytics integration manager instance
_analytics_manager: Optional[AnalyticsIntegrationManager] = None


def get_analytics_integration_manager() -> AnalyticsIntegrationManager:
    """Get the global analytics integration manager instance."""
    global _analytics_manager
    if _analytics_manager is None:
        _analytics_manager = AnalyticsIntegrationManager()
    return _analytics_manager


__all__ = [
    'AnalysisType',
    'InsightPriority',
    'InsightCategory',
    'AnalysisInsight',
    'AnalysisWorkflow',
    'AnalyticsIntegrationManager',
    'get_analytics_integration_manager'
]
