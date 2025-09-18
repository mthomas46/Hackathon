"""Benefit Calculation - Advanced Value Assessment Using Ecosystem Metrics.

This module implements sophisticated benefit calculation algorithms that quantify
the value and impact of the Project Simulation Service using comprehensive metrics
from across the ecosystem, providing data-driven insights into ROI and effectiveness.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.content.context_aware_generation import ContentContext
from simulation.infrastructure.integration.service_clients import get_ecosystem_client


class BenefitCategory(Enum):
    """Categories of benefits that can be calculated."""
    PRODUCTIVITY = "productivity"
    QUALITY = "quality"
    RISK_REDUCTION = "risk_reduction"
    COST_SAVINGS = "cost_savings"
    TIME_EFFICIENCY = "time_efficiency"
    KNOWLEDGE_VALUE = "knowledge_value"
    INNOVATION_IMPACT = "innovation_impact"
    TEAM_DEVELOPMENT = "team_development"


class BenefitType(Enum):
    """Types of benefits that can be measured."""
    DIRECT_SAVINGS = "direct_savings"
    INDIRECT_SAVINGS = "indirect_savings"
    PREVENTION_COSTS = "prevention_costs"
    PRODUCTIVITY_IMPROVEMENT = "productivity_improvement"
    QUALITY_ENHANCEMENT = "quality_enhancement"
    RISK_MITIGATION = "risk_mitigation"
    KNOWLEDGE_ACCUMULATION = "knowledge_accumulation"
    INNOVATION_ACCELERATION = "innovation_acceleration"


class BenefitMetric:
    """Represents a benefit metric with its calculation method."""

    def __init__(self,
                 metric_id: str,
                 name: str,
                 category: BenefitCategory,
                 benefit_type: BenefitType,
                 calculation_method: str,
                 baseline_value: Optional[float] = None,
                 target_value: Optional[float] = None,
                 unit: str = "units",
                 description: str = ""):
        """Initialize benefit metric."""
        self.metric_id = metric_id
        self.name = name
        self.category = category
        self.benefit_type = benefit_type
        self.calculation_method = calculation_method
        self.baseline_value = baseline_value
        self.target_value = target_value
        self.unit = unit
        self.description = description

    def calculate_benefit(self, current_value: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate benefit for this metric."""
        if self.baseline_value is None:
            return {"benefit_value": 0.0, "benefit_percentage": 0.0, "confidence": 0.0}

        benefit_value = current_value - self.baseline_value
        benefit_percentage = (benefit_value / self.baseline_value) * 100 if self.baseline_value != 0 else 0.0

        # Calculate confidence based on data quality and sample size
        confidence = self._calculate_confidence(context)

        return {
            "benefit_value": benefit_value,
            "benefit_percentage": benefit_percentage,
            "confidence": confidence,
            "current_value": current_value,
            "baseline_value": self.baseline_value,
            "unit": self.unit
        }

    def _calculate_confidence(self, context: Dict[str, Any]) -> float:
        """Calculate confidence level for the benefit calculation."""
        # Base confidence
        confidence = 0.7

        # Adjust based on data points
        data_points = context.get("data_points", 1)
        if data_points > 10:
            confidence += 0.1
        elif data_points < 3:
            confidence -= 0.2

        # Adjust based on time span
        time_span_days = context.get("time_span_days", 1)
        if time_span_days > 30:
            confidence += 0.1
        elif time_span_days < 7:
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))


class BenefitCalculator:
    """Calculates benefits and ROI using ecosystem metrics."""

    def __init__(self):
        """Initialize benefit calculator."""
        self.logger = get_simulation_logger()

        # Service clients for metric collection
        self.analysis_client = get_ecosystem_client("analysis_service")
        self.doc_store_client = get_ecosystem_client("doc_store")
        self.llm_client = get_ecosystem_client("llm_gateway")

        # Benefit metrics definitions
        self.benefit_metrics = self._define_benefit_metrics()

        # Historical benefit data
        self.benefit_history: List[Dict[str, Any]] = []

        # Cost assumptions (configurable)
        self.cost_assumptions = {
            "developer_hourly_rate": 75.0,  # USD per hour
            "quality_assurance_hourly_rate": 65.0,
            "project_manager_hourly_rate": 85.0,
            "infrastructure_cost_per_hour": 2.5,
            "risk_mitigation_cost_factor": 0.15,  # Percentage of project cost
            "knowledge_value_multiplier": 1.5,  # Multiplier for knowledge benefits
            "innovation_value_multiplier": 2.0  # Multiplier for innovation benefits
        }

    def _define_benefit_metrics(self) -> Dict[str, BenefitMetric]:
        """Define comprehensive benefit metrics."""
        metrics = {}

        # Productivity Metrics
        metrics["development_velocity"] = BenefitMetric(
            metric_id="development_velocity",
            name="Development Velocity",
            category=BenefitCategory.PRODUCTIVITY,
            benefit_type=BenefitType.PRODUCTIVITY_IMPROVEMENT,
            calculation_method="story_points_per_sprint",
            baseline_value=25.0,  # Story points per sprint
            target_value=35.0,
            unit="story points",
            description="Improvement in development velocity through better planning and simulation"
        )

        metrics["code_quality_score"] = BenefitMetric(
            metric_id="code_quality_score",
            name="Code Quality Score",
            category=BenefitCategory.QUALITY,
            benefit_type=BenefitType.QUALITY_ENHANCEMENT,
            calculation_method="static_analysis_score",
            baseline_value=7.5,  # Out of 10
            target_value=9.0,
            unit="quality points",
            description="Improvement in code quality through early defect detection"
        )

        metrics["defect_detection_efficiency"] = BenefitMetric(
            metric_id="defect_detection_efficiency",
            name="Defect Detection Efficiency",
            category=BenefitCategory.QUALITY,
            benefit_type=BenefitType.PREVENTION_COSTS,
            calculation_method="defects_prevented_per_hour",
            baseline_value=2.5,
            target_value=4.0,
            unit="defects prevented",
            description="Efficiency in detecting and preventing defects before production"
        )

        # Time Efficiency Metrics
        metrics["requirements_stability"] = BenefitMetric(
            metric_id="requirements_stability",
            name="Requirements Stability",
            category=BenefitCategory.TIME_EFFICIENCY,
            benefit_type=BenefitType.INDIRECT_SAVINGS,
            calculation_method="change_request_reduction",
            baseline_value=15.0,  # Percentage of requirements changed
            target_value=5.0,
            unit="percentage",
            description="Reduction in requirements changes through better upfront analysis"
        )

        metrics["project_planning_accuracy"] = BenefitMetric(
            metric_id="project_planning_accuracy",
            name="Project Planning Accuracy",
            category=BenefitCategory.TIME_EFFICIENCY,
            benefit_type=BenefitType.INDIRECT_SAVINGS,
            calculation_method="estimation_accuracy_improvement",
            baseline_value=70.0,  # Percentage accuracy
            target_value=90.0,
            unit="percentage",
            description="Improvement in project estimation accuracy"
        )

        # Risk Reduction Metrics
        metrics["risk_identification_coverage"] = BenefitMetric(
            metric_id="risk_identification_coverage",
            name="Risk Identification Coverage",
            category=BenefitCategory.RISK_REDUCTION,
            benefit_type=BenefitType.RISK_MITIGATION,
            calculation_method="risks_identified_percentage",
            baseline_value=60.0,  # Percentage of risks identified
            target_value=95.0,
            unit="percentage",
            description="Coverage of risk identification and mitigation planning"
        )

        metrics["incident_prevention_rate"] = BenefitMetric(
            metric_id="incident_prevention_rate",
            name="Incident Prevention Rate",
            category=BenefitCategory.RISK_REDUCTION,
            benefit_type=BenefitType.PREVENTION_COSTS,
            calculation_method="production_incidents_prevented",
            baseline_value=3,  # Incidents prevented per quarter
            target_value=8,
            unit="incidents",
            description="Production incidents prevented through proactive risk management"
        )

        # Knowledge and Learning Metrics
        metrics["knowledge_sharing_efficiency"] = BenefitMetric(
            metric_id="knowledge_sharing_efficiency",
            name="Knowledge Sharing Efficiency",
            category=BenefitCategory.KNOWLEDGE_VALUE,
            benefit_type=BenefitType.KNOWLEDGE_ACCUMULATION,
            calculation_method="knowledge_transfer_rate",
            baseline_value=40.0,  # Percentage of knowledge effectively shared
            target_value=80.0,
            unit="percentage",
            description="Efficiency of knowledge sharing and institutional learning"
        )

        metrics["onboarding_time_reduction"] = BenefitMetric(
            metric_id="onboarding_time_reduction",
            name="Onboarding Time Reduction",
            category=BenefitCategory.TEAM_DEVELOPMENT,
            benefit_type=BenefitType.INDIRECT_SAVINGS,
            calculation_method="new_hire_ramp_up_days",
            baseline_value=30,  # Days to ramp up new hire
            target_value=15,
            unit="days",
            description="Reduction in time for new team members to become productive"
        )

        # Innovation Metrics
        metrics["innovation_acceleration"] = BenefitMetric(
            metric_id="innovation_acceleration",
            name="Innovation Acceleration",
            category=BenefitCategory.INNOVATION_IMPACT,
            benefit_type=BenefitType.INNOVATION_ACCELERATION,
            calculation_method="new_solutions_per_quarter",
            baseline_value=2,  # New innovative solutions per quarter
            target_value=6,
            unit="solutions",
            description="Acceleration of innovation through simulation and experimentation"
        )

        return metrics

    async def calculate_project_benefits(self,
                                       project_context: ContentContext,
                                       analysis_results: Dict[str, Any],
                                       time_period_days: int = 90) -> Dict[str, Any]:
        """Calculate comprehensive benefits for a project."""
        try:
            self.logger.info("Calculating project benefits",
                           project_id=project_context.project_config.get("id"),
                           time_period=time_period_days)

            # Collect relevant metrics from analysis results
            collected_metrics = await self._collect_ecosystem_metrics(project_context, time_period_days)

            # Calculate benefits for each metric
            benefit_calculations = {}
            for metric_id, metric in self.benefit_metrics.items():
                if metric_id in collected_metrics:
                    current_value = collected_metrics[metric_id]["value"]
                    context_data = collected_metrics[metric_id]["context"]

                    benefit_result = metric.calculate_benefit(current_value, context_data)
                    benefit_calculations[metric_id] = {
                        "metric": metric,
                        "calculation": benefit_result
                    }

            # Aggregate benefits by category
            category_benefits = self._aggregate_benefits_by_category(benefit_calculations)

            # Calculate total ROI
            total_roi = self._calculate_total_roi(benefit_calculations, project_context)

            # Calculate benefit realization timeline
            realization_timeline = self._calculate_benefit_realization_timeline(benefit_calculations)

            # Generate benefit insights
            benefit_insights = self._generate_benefit_insights(benefit_calculations, category_benefits)

            result = {
                "project_id": project_context.project_config.get("id"),
                "calculation_period_days": time_period_days,
                "total_roi": total_roi,
                "category_benefits": category_benefits,
                "individual_metrics": benefit_calculations,
                "realization_timeline": realization_timeline,
                "benefit_insights": benefit_insights,
                "confidence_score": self._calculate_overall_confidence(benefit_calculations),
                "generated_at": datetime.now(),
                "methodology": "ecosystem_metrics_based_calculation"
            }

            # Store in history for trend analysis
            self.benefit_history.append(result)

            return result

        except Exception as e:
            self.logger.error("Benefit calculation failed", error=str(e))
            return {
                "error": str(e),
                "status": "calculation_failed",
                "generated_at": datetime.now()
            }

    async def _collect_ecosystem_metrics(self,
                                       project_context: ContentContext,
                                       time_period_days: int) -> Dict[str, Any]:
        """Collect relevant metrics from across the ecosystem."""
        collected_metrics = {}

        try:
            # Collect productivity metrics
            productivity_data = await self._collect_productivity_metrics(project_context, time_period_days)
            collected_metrics.update(productivity_data)

            # Collect quality metrics
            quality_data = await self._collect_quality_metrics(project_context, time_period_days)
            collected_metrics.update(quality_data)

            # Collect risk metrics
            risk_data = await self._collect_risk_metrics(project_context, time_period_days)
            collected_metrics.update(risk_data)

            # Collect time efficiency metrics
            time_data = await self._collect_time_efficiency_metrics(project_context, time_period_days)
            collected_metrics.update(time_data)

            # Collect knowledge metrics
            knowledge_data = await self._collect_knowledge_metrics(project_context, time_period_days)
            collected_metrics.update(knowledge_data)

        except Exception as e:
            self.logger.warning("Metric collection partially failed", error=str(e))

        return collected_metrics

    async def _collect_productivity_metrics(self,
                                          project_context: ContentContext,
                                          time_period_days: int) -> Dict[str, Any]:
        """Collect productivity-related metrics."""
        metrics = {}

        # Development velocity (story points completed)
        # This would integrate with project management tools
        metrics["development_velocity"] = {
            "value": project_context.project_config.get("average_velocity", 30.0),
            "context": {"data_points": 12, "time_span_days": time_period_days}
        }

        # Code quality score from analysis service
        try:
            quality_analysis = await self.analysis_client.get_code_quality_metrics(
                project_id=project_context.project_config.get("id"),
                time_period_days=time_period_days
            )
            metrics["code_quality_score"] = {
                "value": quality_analysis.get("overall_score", 8.0),
                "context": {"data_points": 10, "time_span_days": time_period_days}
            }
        except:
            metrics["code_quality_score"] = {
                "value": 8.0,  # Fallback value
                "context": {"data_points": 1, "time_span_days": time_period_days}
            }

        return metrics

    async def _collect_quality_metrics(self,
                                     project_context: ContentContext,
                                     time_period_days: int) -> Dict[str, Any]:
        """Collect quality-related metrics."""
        metrics = {}

        # Defect detection efficiency
        metrics["defect_detection_efficiency"] = {
            "value": project_context.project_config.get("defect_detection_rate", 3.5),
            "context": {"data_points": 8, "time_span_days": time_period_days}
        }

        return metrics

    async def _collect_risk_metrics(self,
                                  project_context: ContentContext,
                                  time_period_days: int) -> Dict[str, Any]:
        """Collect risk-related metrics."""
        metrics = {}

        # Risk identification coverage
        metrics["risk_identification_coverage"] = {
            "value": project_context.project_config.get("risk_coverage", 85.0),
            "context": {"data_points": 6, "time_span_days": time_period_days}
        }

        # Incident prevention rate
        metrics["incident_prevention_rate"] = {
            "value": project_context.project_config.get("incidents_prevented", 5),
            "context": {"data_points": 4, "time_span_days": time_period_days}
        }

        return metrics

    async def _collect_time_efficiency_metrics(self,
                                             project_context: ContentContext,
                                             time_period_days: int) -> Dict[str, Any]:
        """Collect time efficiency metrics."""
        metrics = {}

        # Requirements stability
        metrics["requirements_stability"] = {
            "value": project_context.project_config.get("requirements_stability", 10.0),
            "context": {"data_points": 5, "time_span_days": time_period_days}
        }

        # Project planning accuracy
        metrics["project_planning_accuracy"] = {
            "value": project_context.project_config.get("planning_accuracy", 85.0),
            "context": {"data_points": 3, "time_span_days": time_period_days}
        }

        return metrics

    async def _collect_knowledge_metrics(self,
                                       project_context: ContentContext,
                                       time_period_days: int) -> Dict[str, Any]:
        """Collect knowledge and learning metrics."""
        metrics = {}

        # Knowledge sharing efficiency
        metrics["knowledge_sharing_efficiency"] = {
            "value": project_context.project_config.get("knowledge_sharing", 70.0),
            "context": {"data_points": 7, "time_span_days": time_period_days}
        }

        # Onboarding time reduction
        metrics["onboarding_time_reduction"] = {
            "value": project_context.project_config.get("onboarding_time", 20),
            "context": {"data_points": 4, "time_span_days": time_period_days}
        }

        # Innovation acceleration
        metrics["innovation_acceleration"] = {
            "value": project_context.project_config.get("innovations_created", 4),
            "context": {"data_points": 3, "time_span_days": time_period_days}
        }

        return metrics

    def _aggregate_benefits_by_category(self, benefit_calculations: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate benefits by category."""
        category_aggregates = {}

        for metric_id, calculation_data in benefit_calculations.items():
            metric = calculation_data["metric"]
            calculation = calculation_data["calculation"]

            category = metric.category.value

            if category not in category_aggregates:
                category_aggregates[category] = {
                    "total_benefit_value": 0.0,
                    "total_benefit_percentage": 0.0,
                    "average_confidence": 0.0,
                    "metric_count": 0,
                    "metrics": []
                }

            category_data = category_aggregates[category]
            category_data["total_benefit_value"] += calculation["benefit_value"]
            category_data["total_benefit_percentage"] += calculation["benefit_percentage"]
            category_data["average_confidence"] += calculation["confidence"]
            category_data["metric_count"] += 1
            category_data["metrics"].append({
                "metric_id": metric_id,
                "name": metric.name,
                "benefit_value": calculation["benefit_value"],
                "benefit_percentage": calculation["benefit_percentage"]
            })

        # Calculate averages
        for category_data in category_aggregates.values():
            if category_data["metric_count"] > 0:
                category_data["average_confidence"] /= category_data["metric_count"]
                category_data["total_benefit_percentage"] /= category_data["metric_count"]

        return category_aggregates

    def _calculate_total_roi(self,
                           benefit_calculations: Dict[str, Any],
                           project_context: ContentContext) -> Dict[str, Any]:
        """Calculate total ROI for the project."""
        # Calculate total benefits
        total_benefits = 0.0
        total_costs = 0.0

        for calculation_data in benefit_calculations.values():
            metric = calculation_data["metric"]
            calculation = calculation_data["calculation"]

            # Convert benefit to monetary value
            benefit_value = self._convert_benefit_to_monetary(calculation, metric)
            total_benefits += benefit_value

        # Estimate implementation costs
        project_duration_weeks = project_context.project_config.get("duration_weeks", 8)
        team_size = len(project_context.team_members)
        total_costs = self._estimate_implementation_costs(project_duration_weeks, team_size)

        # Calculate ROI
        if total_costs > 0:
            roi_percentage = ((total_benefits - total_costs) / total_costs) * 100
            payback_period_months = (total_costs / (total_benefits / 12)) if total_benefits > 0 else 0
        else:
            roi_percentage = 0.0
            payback_period_months = 0

        return {
            "total_benefits": total_benefits,
            "total_costs": total_costs,
            "net_benefits": total_benefits - total_costs,
            "roi_percentage": roi_percentage,
            "payback_period_months": payback_period_months,
            "benefit_cost_ratio": total_benefits / total_costs if total_costs > 0 else 0
        }

    def _convert_benefit_to_monetary(self, calculation: Dict[str, Any], metric: BenefitMetric) -> float:
        """Convert benefit calculation to monetary value."""
        benefit_value = calculation["benefit_value"]

        # Apply category-specific multipliers
        if metric.category == BenefitCategory.PRODUCTIVITY:
            # Productivity improvements save developer time
            return benefit_value * self.cost_assumptions["developer_hourly_rate"] * 8  # 8 hours per day

        elif metric.category == BenefitCategory.QUALITY:
            # Quality improvements reduce defect fixing costs
            return benefit_value * self.cost_assumptions["developer_hourly_rate"] * 4  # 4 hours to fix defect

        elif metric.category == BenefitCategory.RISK_REDUCTION:
            # Risk reduction saves incident response costs
            return benefit_value * 5000  # Average incident cost

        elif metric.category == BenefitCategory.TIME_EFFICIENCY:
            # Time efficiency saves project management time
            return benefit_value * self.cost_assumptions["project_manager_hourly_rate"] * 8

        elif metric.category == BenefitCategory.KNOWLEDGE_VALUE:
            # Knowledge value has long-term benefits
            return benefit_value * self.cost_assumptions["knowledge_value_multiplier"] * 1000

        elif metric.category == BenefitCategory.INNOVATION_IMPACT:
            # Innovation creates significant value
            return benefit_value * self.cost_assumptions["innovation_value_multiplier"] * 10000

        else:
            # Default conversion
            return benefit_value * 100  # Generic conversion

    def _estimate_implementation_costs(self, duration_weeks: int, team_size: int) -> float:
        """Estimate implementation costs."""
        # Developer costs
        developer_costs = (duration_weeks * 5 * 8 * self.cost_assumptions["developer_hourly_rate"] * team_size)

        # Infrastructure costs
        infrastructure_costs = (duration_weeks * 5 * 8 * self.cost_assumptions["infrastructure_cost_per_hour"] * team_size)

        # Training and adoption costs (20% of total)
        training_costs = (developer_costs + infrastructure_costs) * 0.2

        return developer_costs + infrastructure_costs + training_costs

    def _calculate_benefit_realization_timeline(self, benefit_calculations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate when benefits will be realized."""
        timeline = {
            "immediate_benefits": [],  # Within 1 month
            "short_term_benefits": [],  # 1-3 months
            "medium_term_benefits": [],  # 3-6 months
            "long_term_benefits": []    # 6+ months
        }

        for metric_id, calculation_data in benefit_calculations.items():
            metric = calculation_data["metric"]
            calculation = calculation_data["calculation"]

            if calculation["benefit_value"] > 0:
                benefit_item = {
                    "metric_id": metric_id,
                    "name": metric.name,
                    "benefit_value": calculation["benefit_value"],
                    "realization_time": self._estimate_realization_time(metric.category)
                }

                realization_time = benefit_item["realization_time"]

                if realization_time <= 30:
                    timeline["immediate_benefits"].append(benefit_item)
                elif realization_time <= 90:
                    timeline["short_term_benefits"].append(benefit_item)
                elif realization_time <= 180:
                    timeline["medium_term_benefits"].append(benefit_item)
                else:
                    timeline["long_term_benefits"].append(benefit_item)

        return timeline

    def _estimate_realization_time(self, category: BenefitCategory) -> int:
        """Estimate realization time in days for a benefit category."""
        realization_times = {
            BenefitCategory.PRODUCTIVITY: 30,      # 1 month
            BenefitCategory.QUALITY: 60,           # 2 months
            BenefitCategory.RISK_REDUCTION: 90,    # 3 months
            BenefitCategory.TIME_EFFICIENCY: 45,   # 1.5 months
            BenefitCategory.KNOWLEDGE_VALUE: 180,  # 6 months
            BenefitCategory.INNOVATION_IMPACT: 120, # 4 months
            BenefitCategory.TEAM_DEVELOPMENT: 90   # 3 months
        }

        return realization_times.get(category, 60)

    def _generate_benefit_insights(self,
                                 benefit_calculations: Dict[str, Any],
                                 category_benefits: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights about the calculated benefits."""
        insights = []

        # Find top benefit categories
        sorted_categories = sorted(
            category_benefits.items(),
            key=lambda x: x[1]["total_benefit_value"],
            reverse=True
        )

        if sorted_categories:
            top_category = sorted_categories[0]
            insights.append({
                "type": "top_benefit_category",
                "title": f"Primary Benefit Area: {top_category[0].replace('_', ' ').title()}",
                "description": f"The largest benefits come from {top_category[0].replace('_', ' ')} improvements",
                "value": top_category[1]["total_benefit_value"],
                "confidence": top_category[1]["average_confidence"]
            })

        # Identify quick wins
        immediate_benefits = []
        for calc_data in benefit_calculations.values():
            metric = calc_data["metric"]
            calculation = calc_data["calculation"]
            if (calculation["benefit_value"] > 0 and
                self._estimate_realization_time(metric.category) <= 30):
                immediate_benefits.append(calc_data)

        if immediate_benefits:
            insights.append({
                "type": "quick_wins",
                "title": f"Quick Wins Available ({len(immediate_benefits)})",
                "description": "Benefits that can be realized within 30 days",
                "count": len(immediate_benefits),
                "total_value": sum(c["calculation"]["benefit_value"] for c in immediate_benefits)
            })

        # Check for high-confidence benefits
        high_confidence_benefits = [
            calc for calc in benefit_calculations.values()
            if calc["calculation"]["confidence"] > 0.8
        ]

        if high_confidence_benefits:
            insights.append({
                "type": "high_confidence_benefits",
                "title": f"High-Confidence Benefits ({len(high_confidence_benefits)})",
                "description": "Benefits with high confidence in realization",
                "count": len(high_confidence_benefits),
                "total_value": sum(c["calculation"]["benefit_value"] for c in high_confidence_benefits)
            })

        return insights

    def _calculate_overall_confidence(self, benefit_calculations: Dict[str, Any]) -> float:
        """Calculate overall confidence in benefit calculations."""
        if not benefit_calculations:
            return 0.0

        confidences = [calc["calculation"]["confidence"] for calc in benefit_calculations.values()]

        return statistics.mean(confidences) if confidences else 0.0

    def get_benefit_trends(self, project_id: Optional[str] = None, months: int = 6) -> Dict[str, Any]:
        """Get benefit trends over time."""
        cutoff_date = datetime.now() - timedelta(days=months*30)

        relevant_history = [
            entry for entry in self.benefit_history
            if (entry.get("generated_at", datetime.min) > cutoff_date and
                (project_id is None or entry.get("project_id") == project_id))
        ]

        if not relevant_history:
            return {"message": "No benefit history available", "trend_analysis": {}}

        # Analyze trends
        trends = {
            "total_roi_trend": [],
            "category_trends": {},
            "metric_trends": {}
        }

        sorted_history = sorted(relevant_history, key=lambda x: x["generated_at"])

        for entry in sorted_history:
            trends["total_roi_trend"].append({
                "date": entry["generated_at"].isoformat(),
                "roi": entry["total_roi"]["roi_percentage"]
            })

        return {
            "analysis_period_months": months,
            "data_points": len(relevant_history),
            "trends": trends,
            "insights": self._analyze_benefit_trends(trends)
        }

    def _analyze_benefit_trends(self, trends: Dict[str, Any]) -> List[str]:
        """Analyze benefit trends and generate insights."""
        insights = []

        roi_trend = trends["total_roi_trend"]
        if len(roi_trend) >= 2:
            first_roi = roi_trend[0]["roi"]
            last_roi = roi_trend[-1]["roi"]

            if last_roi > first_roi:
                improvement = ((last_roi - first_roi) / abs(first_roi)) * 100 if first_roi != 0 else 0
                insights.append(f"ROI improved by {improvement:.1f}% over the analysis period")
            else:
                decline = ((first_roi - last_roi) / abs(first_roi)) * 100 if first_roi != 0 else 0
                insights.append(f"ROI declined by {decline:.1f}% over the analysis period")

        return insights


# Global benefit calculator instance
_benefit_calculator: Optional[BenefitCalculator] = None


def get_benefit_calculator() -> BenefitCalculator:
    """Get the global benefit calculator instance."""
    global _benefit_calculator
    if _benefit_calculator is None:
        _benefit_calculator = BenefitCalculator()
    return _benefit_calculator


__all__ = [
    'BenefitCategory',
    'BenefitType',
    'BenefitMetric',
    'BenefitCalculator',
    'get_benefit_calculator'
]
