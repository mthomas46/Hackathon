"""
Feature Planning Service - Domain service for feature analysis and planning
===========================================================================

Provides business logic for feature analysis, AI-powered decomposition,
risk assessment, and planning coordination.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from ..entities.feature import Feature, FeatureStatus, FeaturePriority


class FeaturePlanningService:
    """
    Domain service for feature planning and analysis.

    Coordinates AI analysis, risk assessment, and feature decomposition
    using integrations with Interpreter, LLM Gateway, and other services.
    """

    def __init__(self, interpreter_client=None, llm_gateway_client=None, source_agent_client=None):
        """Initialize with service clients."""
        self.interpreter_client = interpreter_client
        self.llm_gateway_client = llm_gateway_client
        self.source_agent_client = source_agent_client

    async def analyze_feature(self, feature: Feature) -> Dict[str, Any]:
        """
        Perform comprehensive AI analysis of a feature.

        Uses multiple AI services to analyze requirements, estimate complexity,
        identify risks, and suggest implementation approaches.
        """
        analysis_results = {
            "requirements_analysis": {},
            "technical_complexity": {},
            "risk_assessment": {},
            "suggested_approach": {},
            "estimated_effort": None,
            "dependencies": [],
            "recommendations": []
        }

        try:
            # Analyze requirements using interpreter
            if self.interpreter_client:
                requirements_analysis = await self._analyze_requirements(feature)
                analysis_results["requirements_analysis"] = requirements_analysis

            # Assess technical complexity
            complexity_analysis = await self._assess_technical_complexity(feature)
            analysis_results["technical_complexity"] = complexity_analysis

            # Perform risk assessment
            risk_analysis = await self._assess_risks(feature)
            analysis_results["risk_assessment"] = risk_analysis

            # Generate implementation recommendations
            recommendations = await self._generate_recommendations(feature, analysis_results)
            analysis_results["recommendations"] = recommendations

            # Estimate effort
            effort_estimate = await self._estimate_effort(feature, analysis_results)
            analysis_results["estimated_effort"] = effort_estimate

        except Exception as e:
            analysis_results["error"] = f"Analysis failed: {str(e)}"

        return analysis_results

    async def _analyze_requirements(self, feature: Feature) -> Dict[str, Any]:
        """Analyze feature requirements using AI."""
        prompt = f"""
        Analyze the following software feature requirements:

        Title: {feature.title}
        Description: {feature.description}
        Acceptance Criteria:
        {chr(10).join(f"- {criterion}" for criterion in feature.acceptance_criteria)}

        Please provide:
        1. Functional requirements breakdown
        2. Non-functional requirements
        3. Edge cases and error scenarios
        4. Integration points
        5. Data requirements
        """

        # This would call the interpreter service
        # For now, return mock analysis
        return {
            "functional_requirements": ["Core functionality", "User interface", "Data processing"],
            "non_functional_requirements": ["Performance", "Security", "Usability"],
            "edge_cases": ["Error handling", "Boundary conditions"],
            "integration_points": ["Database", "External APIs"],
            "data_requirements": ["User data", "Configuration data"]
        }

    async def _assess_technical_complexity(self, feature: Feature) -> Dict[str, Any]:
        """Assess technical complexity of the feature."""
        # Analyze based on description keywords and acceptance criteria
        complexity_indicators = {
            "low": ["simple", "basic", "standard", "straightforward"],
            "medium": ["complex", "multiple", "integration", "custom"],
            "high": ["advanced", "sophisticated", "distributed", "real-time", "machine learning"]
        }

        text_to_analyze = f"{feature.title} {feature.description} {' '.join(feature.acceptance_criteria)}".lower()

        complexity_score = 1  # Default low
        for level, indicators in complexity_indicators.items():
            if any(indicator in text_to_analyze for indicator in indicators):
                if level == "medium":
                    complexity_score = 2
                elif level == "high":
                    complexity_score = 3

        return {
            "complexity_score": complexity_score,
            "complexity_level": "low" if complexity_score == 1 else "medium" if complexity_score == 2 else "high",
            "factors": ["Technical requirements", "Integration complexity", "Data processing needs"]
        }

    async def _assess_risks(self, feature: Feature) -> Dict[str, Any]:
        """Assess risks associated with feature implementation."""
        risks = []

        # Check for common risk indicators
        risk_indicators = {
            "Security risk": ["authentication", "authorization", "encryption", "sensitive data"],
            "Performance risk": ["real-time", "high volume", "concurrent users", "large datasets"],
            "Integration risk": ["external api", "third-party", "legacy system", "distributed"],
            "Data risk": ["migration", "data integrity", "backup", "recovery"],
            "Compliance risk": ["regulatory", "gdpr", "hipaa", "audit"]
        }

        text_to_analyze = f"{feature.title} {feature.description} {' '.join(feature.acceptance_criteria)}".lower()

        for risk_type, indicators in risk_indicators.items():
            if any(indicator in text_to_analyze for indicator in indicators):
                risks.append({
                    "type": risk_type,
                    "severity": "medium",
                    "description": f"Feature involves {risk_type.lower()} considerations",
                    "mitigation": f"Implement appropriate {risk_type.lower()} measures"
                })

        return {
            "identified_risks": risks,
            "overall_risk_level": "low" if len(risks) == 0 else "medium" if len(risks) <= 2 else "high",
            "risk_score": len(risks)
        }

    async def _generate_recommendations(self, feature: Feature, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate implementation recommendations."""
        recommendations = []

        # Based on complexity
        complexity = analysis_results.get("technical_complexity", {}).get("complexity_score", 1)
        if complexity >= 3:
            recommendations.append({
                "type": "architecture_review",
                "priority": "high",
                "description": "Conduct architecture review for high-complexity feature",
                "rationale": "Complex features require careful architectural planning"
            })

        # Based on risks
        risks = analysis_results.get("risk_assessment", {}).get("identified_risks", [])
        if len(risks) > 0:
            recommendations.append({
                "type": "security_review",
                "priority": "high",
                "description": "Include security review in development process",
                "rationale": f"Feature has {len(risks)} identified risk areas"
            })

        # Always include testing recommendations
        recommendations.append({
            "type": "testing_strategy",
            "priority": "medium",
            "description": "Develop comprehensive testing strategy",
            "rationale": "Ensure feature quality and reliability"
        })

        return recommendations

    async def _estimate_effort(self, feature: Feature, analysis_results: Dict[str, Any]) -> Optional[float]:
        """Estimate development effort in story points."""
        base_effort = 5  # Default medium effort

        # Adjust based on complexity
        complexity = analysis_results.get("technical_complexity", {}).get("complexity_score", 1)
        if complexity == 2:
            base_effort = 8
        elif complexity == 3:
            base_effort = 13

        # Adjust based on acceptance criteria count
        criteria_count = len(feature.acceptance_criteria)
        if criteria_count > 5:
            base_effort += 2
        elif criteria_count > 10:
            base_effort += 5

        # Adjust based on risks
        risks = analysis_results.get("risk_assessment", {}).get("risk_score", 0)
        base_effort += risks * 2

        return float(base_effort)

    async def decompose_feature(self, feature: Feature) -> List[Dict[str, Any]]:
        """
        Decompose feature into actionable tasks.

        Uses AI to break down the feature into specific, implementable tasks
        with clear deliverables and acceptance criteria.
        """
        tasks = []

        # Basic task decomposition based on feature type
        if "api" in feature.title.lower() or "api" in feature.description.lower():
            tasks.extend([
                {
                    "title": "Design API endpoints",
                    "description": "Define REST API endpoints with request/response schemas",
                    "type": "design",
                    "estimated_hours": 8
                },
                {
                    "title": "Implement API endpoints",
                    "description": "Develop backend API endpoints with business logic",
                    "type": "development",
                    "estimated_hours": 16
                },
                {
                    "title": "Add API tests",
                    "description": "Create unit and integration tests for API endpoints",
                    "type": "testing",
                    "estimated_hours": 8
                }
            ])

        elif "ui" in feature.title.lower() or "interface" in feature.description.lower():
            tasks.extend([
                {
                    "title": "Design user interface",
                    "description": "Create UI mockups and wireframes",
                    "type": "design",
                    "estimated_hours": 12
                },
                {
                    "title": "Implement UI components",
                    "description": "Develop frontend components and interactions",
                    "type": "development",
                    "estimated_hours": 20
                },
                {
                    "title": "UI testing and polish",
                    "description": "Cross-browser testing and UI refinements",
                    "type": "testing",
                    "estimated_hours": 10
                }
            ])

        else:
            # Generic task breakdown
            tasks.extend([
                {
                    "title": "Requirements analysis",
                    "description": "Detailed analysis of feature requirements",
                    "type": "analysis",
                    "estimated_hours": 6
                },
                {
                    "title": "Technical design",
                    "description": "Design implementation approach and architecture",
                    "type": "design",
                    "estimated_hours": 10
                },
                {
                    "title": "Implementation",
                    "description": "Develop the feature functionality",
                    "type": "development",
                    "estimated_hours": 24
                },
                {
                    "title": "Testing",
                    "description": "Unit tests, integration tests, and validation",
                    "type": "testing",
                    "estimated_hours": 12
                }
            ])

        return tasks

    async def validate_feature_readiness(self, feature: Feature) -> Dict[str, Any]:
        """Validate if feature is ready for planning."""
        issues = []

        if not feature.title:
            issues.append("Feature title is required")

        if not feature.description:
            issues.append("Feature description is required")

        if not feature.acceptance_criteria:
            issues.append("At least one acceptance criterion is required")

        if not feature.business_value:
            issues.append("Business value justification is recommended")

        return {
            "is_ready": len(issues) == 0,
            "issues": issues,
            "readiness_score": max(0, 100 - (len(issues) * 20))
        }
