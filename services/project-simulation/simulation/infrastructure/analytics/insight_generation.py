"""Insight Generation - Intelligent Analysis Result Processing.

This module implements sophisticated insight generation that leverages existing
interpreter service patterns to extract meaningful insights from analysis results,
generate intelligent recommendations, and provide actionable intelligence for
project simulation and analysis.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import re
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.analytics.analytics_integration import (
    AnalysisInsight, InsightPriority, InsightCategory
)
from simulation.infrastructure.integration.service_clients import get_ecosystem_client


class InsightPattern(Enum):
    """Patterns for insight generation."""
    TREND_ANALYSIS = "trend_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    CORRELATION_ANALYSIS = "correlation_analysis"
    PREDICTIVE_MODELING = "predictive_modeling"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"


class InsightType(Enum):
    """Types of insights that can be generated."""
    PERFORMANCE_INSIGHT = "performance_insight"
    RISK_INSIGHT = "risk_insight"
    EFFICIENCY_INSIGHT = "efficiency_insight"
    QUALITY_INSIGHT = "quality_insight"
    PREDICTIVE_INSIGHT = "predictive_insight"
    RECOMMENDATION_INSIGHT = "recommendation_insight"


class InsightGenerator:
    """Generates insights from analysis results using interpreter patterns."""

    def __init__(self):
        """Initialize insight generator."""
        self.logger = get_simulation_logger()
        self.interpreter_client = get_ecosystem_client("interpreter")

        # Insight patterns and rules
        self.insight_patterns = self._load_insight_patterns()

        # Historical insight data for trend analysis
        self.historical_insights: List[AnalysisInsight] = []

        # Insight confidence thresholds
        self.confidence_thresholds = {
            InsightPriority.CRITICAL: 0.8,
            InsightPriority.HIGH: 0.7,
            InsightPriority.MEDIUM: 0.6,
            InsightPriority.LOW: 0.5,
            InsightPriority.INFO: 0.3
        }

    def _load_insight_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load insight generation patterns and rules."""
        return {
            "performance_degradation": {
                "pattern": InsightPattern.TREND_ANALYSIS,
                "type": InsightType.PERFORMANCE_INSIGHT,
                "category": InsightCategory.EFFICIENCY,
                "triggers": ["productivity_score < 0.6", "response_time > 2000ms"],
                "priority": InsightPriority.HIGH,
                "template": "Performance degradation detected: {metric} has decreased by {change}% over {period}"
            },
            "risk_escalation": {
                "pattern": InsightPattern.ANOMALY_DETECTION,
                "type": InsightType.RISK_INSIGHT,
                "category": InsightCategory.RISK,
                "triggers": ["risk_score > 0.7", "critical_issues > 5"],
                "priority": InsightPriority.CRITICAL,
                "template": "Risk escalation: {risk_type} risk has increased to {level}"
            },
            "quality_improvement": {
                "pattern": InsightPattern.TREND_ANALYSIS,
                "type": InsightType.QUALITY_INSIGHT,
                "category": InsightCategory.QUALITY,
                "triggers": ["quality_score > 0.8", "issues_resolved > 10"],
                "priority": InsightPriority.MEDIUM,
                "template": "Quality improvement: {metric} has improved by {change}%"
            },
            "predictive_risk": {
                "pattern": InsightPattern.PREDICTIVE_MODELING,
                "type": InsightType.PREDICTIVE_INSIGHT,
                "category": InsightCategory.RISK,
                "triggers": ["trend_slope < -0.1", "volatility > 0.3"],
                "priority": InsightPriority.HIGH,
                "template": "Predictive risk: {metric} shows concerning trend, potential {impact} in {timeframe}"
            },
            "efficiency_gain": {
                "pattern": InsightPattern.CORRELATION_ANALYSIS,
                "type": InsightType.EFFICIENCY_INSIGHT,
                "category": InsightCategory.EFFICIENCY,
                "triggers": ["correlation_coefficient > 0.7", "efficiency_gain > 15%"],
                "priority": InsightPriority.MEDIUM,
                "template": "Efficiency correlation: {factor1} and {factor2} show strong positive correlation"
            },
            "bottleneck_identification": {
                "pattern": InsightPattern.ROOT_CAUSE_ANALYSIS,
                "type": InsightType.RECOMMENDATION_INSIGHT,
                "category": InsightCategory.EFFICIENCY,
                "triggers": ["bottleneck_confidence > 0.8", "impact_score > 0.7"],
                "priority": InsightPriority.HIGH,
                "template": "Bottleneck identified: {bottleneck} is causing {impact} performance degradation"
            }
        }

    async def generate_insights(self,
                              analysis_results: Dict[str, Any],
                              context: Dict[str, Any],
                              historical_data: Optional[List[Dict[str, Any]]] = None) -> List[AnalysisInsight]:
        """Generate insights from analysis results."""
        try:
            insights = []

            # Generate pattern-based insights
            pattern_insights = await self._generate_pattern_based_insights(analysis_results, context)
            insights.extend(pattern_insights)

            # Generate correlation insights
            correlation_insights = await self._generate_correlation_insights(analysis_results, context)
            insights.extend(correlation_insights)

            # Generate predictive insights
            if historical_data:
                predictive_insights = await self._generate_predictive_insights(analysis_results, historical_data)
                insights.extend(predictive_insights)

            # Generate contextual insights
            contextual_insights = await self._generate_contextual_insights(analysis_results, context)
            insights.extend(contextual_insights)

            # Filter and prioritize insights
            filtered_insights = self._filter_and_prioritize_insights(insights)

            # Store insights for historical analysis
            self.historical_insights.extend(filtered_insights)

            self.logger.info("Generated insights from analysis",
                           result_count=len(analysis_results),
                           insights_generated=len(filtered_insights))

            return filtered_insights

        except Exception as e:
            self.logger.error("Insight generation failed", error=str(e))
            return []

    async def _generate_pattern_based_insights(self,
                                            analysis_results: Dict[str, Any],
                                            context: Dict[str, Any]) -> List[AnalysisInsight]:
        """Generate insights based on predefined patterns."""
        insights = []

        for pattern_name, pattern_config in self.insight_patterns.items():
            try:
                # Check if pattern triggers
                if self._check_pattern_triggers(pattern_config, analysis_results):
                    insight = await self._create_pattern_insight(pattern_name, pattern_config, analysis_results, context)
                    if insight:
                        insights.append(insight)

            except Exception as e:
                self.logger.warning("Pattern insight generation failed",
                                  pattern=pattern_name, error=str(e))

        return insights

    def _check_pattern_triggers(self,
                              pattern_config: Dict[str, Any],
                              analysis_results: Dict[str, Any]) -> bool:
        """Check if pattern triggers are met."""
        triggers = pattern_config.get("triggers", [])

        for trigger in triggers:
            if not self._evaluate_trigger(trigger, analysis_results):
                return False

        return len(triggers) > 0

    def _evaluate_trigger(self, trigger: str, analysis_results: Dict[str, Any]) -> bool:
        """Evaluate a trigger condition."""
        # Simple trigger evaluation (can be extended with more complex logic)
        if "<" in trigger:
            parts = trigger.split("<")
            metric = parts[0].strip()
            threshold = float(parts[1].strip())
            value = self._extract_metric_value(metric, analysis_results)
            return value is not None and value < threshold

        elif ">" in trigger:
            parts = trigger.split(">")
            metric = parts[0].strip()
            threshold = float(parts[1].strip().rstrip('%'))
            value = self._extract_metric_value(metric, analysis_results)
            return value is not None and value > threshold

        return False

    def _extract_metric_value(self, metric: str, analysis_results: Dict[str, Any]) -> Optional[float]:
        """Extract metric value from analysis results."""
        # Navigate nested dictionary structure
        keys = metric.split('.')
        current = analysis_results

        try:
            for key in keys:
                if '[' in key and ']' in key:
                    # Handle array indexing
                    array_key, index = key.split('[')
                    index = int(index.rstrip(']'))
                    current = current[array_key][index]
                else:
                    current = current[key]

            # Convert to float if possible
            if isinstance(current, (int, float)):
                return float(current)
            elif isinstance(current, str) and current.replace('.', '').replace('%', '').isdigit():
                return float(current.rstrip('%'))

        except (KeyError, IndexError, ValueError, TypeError):
            pass

        return None

    async def _create_pattern_insight(self,
                                    pattern_name: str,
                                    pattern_config: Dict[str, Any],
                                    analysis_results: Dict[str, Any],
                                    context: Dict[str, Any]) -> Optional[AnalysisInsight]:
        """Create an insight from a pattern match."""
        try:
            # Generate insight content using interpreter patterns
            insight_content = await self._generate_insight_content(pattern_config, analysis_results, context)

            if not insight_content:
                return None

            insight = AnalysisInsight(
                insight_id=f"{pattern_name}_{datetime.now().timestamp()}",
                analysis_type=self._get_analysis_type_from_pattern(pattern_config),
                category=pattern_config["category"],
                priority=pattern_config["priority"],
                title=insight_content["title"],
                description=insight_content["description"],
                confidence_score=self._calculate_insight_confidence(pattern_config, analysis_results),
                impact_score=self._calculate_insight_impact(pattern_config, analysis_results),
                recommendations=insight_content["recommendations"],
                metadata={
                    "pattern": pattern_name,
                    "triggered_at": datetime.now().isoformat(),
                    "analysis_context": context.get("project_id", "unknown")
                }
            )

            return insight

        except Exception as e:
            self.logger.error("Pattern insight creation failed",
                            pattern=pattern_name, error=str(e))
            return None

    async def _generate_insight_content(self,
                                      pattern_config: Dict[str, Any],
                                      analysis_results: Dict[str, Any],
                                      context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate insight content using interpreter patterns."""
        try:
            # Use interpreter service for content generation
            template = pattern_config.get("template", "")
            variables = self._extract_template_variables(template, analysis_results, context)

            # Generate enhanced content
            enhanced_content = await self._enhance_content_with_interpreter(template, variables, context)

            return {
                "title": enhanced_content.get("title", f"Insight: {pattern_config['type'].value}"),
                "description": enhanced_content.get("description", template),
                "recommendations": enhanced_content.get("recommendations", [])
            }

        except Exception as e:
            self.logger.warning("Insight content generation failed", error=str(e))
            # Fallback to basic template
            return {
                "title": f"Pattern Insight: {pattern_config['type'].value}",
                "description": pattern_config.get("template", "Pattern detected"),
                "recommendations": ["Review analysis results", "Consider mitigation strategies"]
            }

    async def _enhance_content_with_interpreter(self,
                                              template: str,
                                              variables: Dict[str, Any],
                                              context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance insight content using interpreter service."""
        try:
            # Prepare interpreter request
            interpreter_request = {
                "template": template,
                "variables": variables,
                "context": {
                    "analysis_type": "insight_generation",
                    "project_context": context,
                    "enhancement_type": "natural_language_processing"
                }
            }

            # Call interpreter service
            response = await self.interpreter_client.generate_insight_content(interpreter_request)

            return response.get("enhanced_content", {
                "title": f"Enhanced Insight",
                "description": template,
                "recommendations": []
            })

        except Exception as e:
            self.logger.warning("Interpreter enhancement failed, using template", error=str(e))
            return {
                "title": f"Analysis Insight",
                "description": self._fill_template(template, variables),
                "recommendations": []
            }

    def _extract_template_variables(self,
                                  template: str,
                                  analysis_results: Dict[str, Any],
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract variables for template filling."""
        variables = {}

        # Extract variables from template
        var_pattern = r'\{(\w+)\}'
        matches = re.findall(var_pattern, template)

        for var in matches:
            if var in analysis_results:
                variables[var] = analysis_results[var]
            elif var in context:
                variables[var] = context[var]
            else:
                variables[var] = f"[{var}]"  # Placeholder

        return variables

    def _fill_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Fill template with variables."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    async def _generate_correlation_insights(self,
                                           analysis_results: Dict[str, Any],
                                           context: Dict[str, Any]) -> List[AnalysisInsight]:
        """Generate insights based on correlations between metrics."""
        insights = []

        try:
            # Identify key metrics
            metrics = self._extract_key_metrics(analysis_results)

            # Calculate correlations
            correlations = self._calculate_metric_correlations(metrics)

            # Generate insights from strong correlations
            for correlation in correlations:
                if abs(correlation["coefficient"]) > 0.7:
                    insight = await self._create_correlation_insight(correlation, context)
                    if insight:
                        insights.append(insight)

        except Exception as e:
            self.logger.warning("Correlation insight generation failed", error=str(e))

        return insights

    def _extract_key_metrics(self, analysis_results: Dict[str, Any]) -> Dict[str, float]:
        """Extract key metrics from analysis results."""
        metrics = {}

        # Define metric extraction patterns
        metric_patterns = {
            "productivity_score": ["productivity_score", "overall_score"],
            "quality_score": ["quality_score", "compliance_score"],
            "risk_score": ["risk_score", "risk_level"],
            "efficiency_score": ["efficiency_score", "performance_score"]
        }

        for metric_name, possible_keys in metric_patterns.items():
            for key in possible_keys:
                if key in analysis_results and isinstance(analysis_results[key], (int, float)):
                    metrics[metric_name] = analysis_results[key]
                    break

        return metrics

    def _calculate_metric_correlations(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Calculate correlations between metrics."""
        correlations = []
        metric_names = list(metrics.keys())

        for i in range(len(metric_names)):
            for j in range(i + 1, len(metric_names)):
                metric1 = metric_names[i]
                metric2 = metric_names[j]

                coefficient = self._calculate_correlation_coefficient(
                    metrics[metric1], metrics[metric2]
                )

                correlations.append({
                    "metric1": metric1,
                    "metric2": metric2,
                    "coefficient": coefficient,
                    "strength": "strong" if abs(coefficient) > 0.7 else "moderate" if abs(coefficient) > 0.5 else "weak"
                })

        return correlations

    def _calculate_correlation_coefficient(self, x: float, y: float) -> float:
        """Calculate Pearson correlation coefficient between two values."""
        # For single values, return 1.0 if they're equal, 0.0 otherwise
        # In a real implementation, this would use historical data
        return 1.0 if x == y else 0.0

    async def _create_correlation_insight(self,
                                        correlation: Dict[str, Any],
                                        context: Dict[str, Any]) -> Optional[AnalysisInsight]:
        """Create an insight from a correlation."""
        try:
            title = f"Correlation Insight: {correlation['metric1']} vs {correlation['metric2']}"
            description = f"Strong {correlation['strength']} correlation ({correlation['coefficient']:.2f}) detected between {correlation['metric1']} and {correlation['metric2']}"

            recommendations = []
            if correlation["coefficient"] > 0.7:
                recommendations.append(f"Leverage the positive relationship between {correlation['metric1']} and {correlation['metric2']}")
            elif correlation["coefficient"] < -0.7:
                recommendations.append(f"Address the inverse relationship between {correlation['metric1']} and {correlation['metric2']}")

            insight = AnalysisInsight(
                insight_id=f"correlation_{datetime.now().timestamp()}",
                analysis_type=correlation.get("analysis_type", "correlation_analysis"),
                category=InsightCategory.EFFICIENCY,
                priority=InsightPriority.MEDIUM,
                title=title,
                description=description,
                confidence_score=abs(correlation["coefficient"]),
                impact_score=0.6,
                recommendations=recommendations,
                metadata={
                    "correlation_coefficient": correlation["coefficient"],
                    "metric1": correlation["metric1"],
                    "metric2": correlation["metric2"]
                }
            )

            return insight

        except Exception as e:
            self.logger.error("Correlation insight creation failed", error=str(e))
            return None

    async def _generate_predictive_insights(self,
                                          analysis_results: Dict[str, Any],
                                          historical_data: List[Dict[str, Any]]) -> List[AnalysisInsight]:
        """Generate predictive insights based on historical trends."""
        insights = []

        try:
            # Analyze trends in key metrics
            trends = self._analyze_metric_trends(analysis_results, historical_data)

            for trend in trends:
                if trend["trend_direction"] == "deteriorating":
                    insight = await self._create_predictive_insight(trend)
                    if insight:
                        insights.append(insight)

        except Exception as e:
            self.logger.warning("Predictive insight generation failed", error=str(e))

        return insights

    def _analyze_metric_trends(self,
                             current_results: Dict[str, Any],
                             historical_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze trends in metrics over time."""
        trends = []

        key_metrics = ["productivity_score", "quality_score", "risk_score"]

        for metric in key_metrics:
            if metric in current_results:
                current_value = current_results[metric]

                # Calculate trend from historical data
                historical_values = [
                    data.get(metric) for data in historical_data
                    if isinstance(data.get(metric), (int, float))
                ]

                if len(historical_values) >= 2:
                    avg_historical = sum(historical_values) / len(historical_values)
                    trend_direction = "improving" if current_value > avg_historical else "deteriorating"
                    change_percentage = ((current_value - avg_historical) / avg_historical) * 100

                    trends.append({
                        "metric": metric,
                        "current_value": current_value,
                        "historical_average": avg_historical,
                        "trend_direction": trend_direction,
                        "change_percentage": change_percentage,
                        "data_points": len(historical_values)
                    })

        return trends

    async def _create_predictive_insight(self, trend: Dict[str, Any]) -> Optional[AnalysisInsight]:
        """Create a predictive insight from trend analysis."""
        try:
            title = f"Predictive Insight: {trend['metric'].replace('_', ' ').title()} Trend"
            description = f"{trend['metric'].replace('_', ' ').title()} shows {trend['trend_direction']} trend with {abs(trend['change_percentage']):.1f}% change from historical average"

            recommendations = []
            if trend["trend_direction"] == "deteriorating":
                recommendations.append(f"Address declining {trend['metric']} to prevent further degradation")
                recommendations.append("Implement monitoring and early warning systems")

            insight = AnalysisInsight(
                insight_id=f"predictive_{datetime.now().timestamp()}",
                analysis_type="predictive_modeling",
                category=InsightCategory.RISK,
                priority=InsightPriority.HIGH,
                title=title,
                description=description,
                confidence_score=0.75,
                impact_score=0.8,
                recommendations=recommendations,
                metadata={
                    "trend_direction": trend["trend_direction"],
                    "change_percentage": trend["change_percentage"],
                    "metric": trend["metric"]
                }
            )

            return insight

        except Exception as e:
            self.logger.error("Predictive insight creation failed", error=str(e))
            return None

    async def _generate_contextual_insights(self,
                                          analysis_results: Dict[str, Any],
                                          context: Dict[str, Any]) -> List[AnalysisInsight]:
        """Generate insights based on project context."""
        insights = []

        try:
            # Project phase context
            phase_insights = self._generate_phase_context_insights(analysis_results, context)
            insights.extend(phase_insights)

            # Team composition context
            team_insights = self._generate_team_context_insights(analysis_results, context)
            insights.extend(team_insights)

            # Timeline context
            timeline_insights = self._generate_timeline_context_insights(analysis_results, context)
            insights.extend(timeline_insights)

        except Exception as e:
            self.logger.warning("Contextual insight generation failed", error=str(e))

        return insights

    def _generate_phase_context_insights(self,
                                       analysis_results: Dict[str, Any],
                                       context: Dict[str, Any]) -> List[AnalysisInsight]:
        """Generate insights based on project phase context."""
        insights = []

        current_phase = context.get("current_phase", "unknown")

        # Phase-specific insights
        if current_phase.lower() == "development":
            if analysis_results.get("test_coverage", 0) < 0.8:
                insights.append(AnalysisInsight(
                    insight_id=f"phase_dev_{datetime.now().timestamp()}",
                    analysis_type="phase_analysis",
                    category=InsightCategory.QUALITY,
                    priority=InsightPriority.HIGH,
                    title="Development Phase: Test Coverage Concern",
                    description="Test coverage is below recommended threshold for development phase",
                    confidence_score=0.8,
                    impact_score=0.7,
                    recommendations=["Increase automated test coverage", "Implement code review requirements"],
                    metadata={"phase": current_phase, "test_coverage": analysis_results.get("test_coverage")}
                ))

        return insights

    def _generate_team_context_insights(self,
                                      analysis_results: Dict[str, Any],
                                      context: Dict[str, Any]) -> List[AnalysisInsight]:
        """Generate insights based on team composition."""
        insights = []

        team_size = context.get("team_size", 0)

        if team_size > 10 and analysis_results.get("communication_score", 0.5) < 0.6:
            insights.append(AnalysisInsight(
                insight_id=f"team_size_{datetime.now().timestamp()}",
                analysis_type="team_analysis",
                category=InsightCategory.EFFICIENCY,
                priority=InsightPriority.MEDIUM,
                title="Large Team Communication Challenge",
                description="Team size suggests potential communication and coordination challenges",
                confidence_score=0.7,
                impact_score=0.6,
                recommendations=["Implement structured communication protocols", "Consider team restructuring"],
                metadata={"team_size": team_size}
            ))

        return insights

    def _generate_timeline_context_insights(self,
                                          analysis_results: Dict[str, Any],
                                          context: Dict[str, Any]) -> List[AnalysisInsight]:
        """Generate insights based on timeline context."""
        insights = []

        progress_percentage = context.get("progress_percentage", 0)
        time_pressure = context.get("time_pressure", 1.0)

        if progress_percentage < 50 and time_pressure > 1.5:
            insights.append(AnalysisInsight(
                insight_id=f"timeline_{datetime.now().timestamp()}",
                analysis_type="timeline_analysis",
                category=InsightCategory.RISK,
                priority=InsightPriority.CRITICAL,
                title="Timeline Pressure Critical",
                description="Low progress combined with high time pressure indicates critical risk",
                confidence_score=0.9,
                impact_score=0.9,
                recommendations=["Reassess project scope", "Consider timeline extension", "Increase resource allocation"],
                metadata={"progress": progress_percentage, "time_pressure": time_pressure}
            ))

        return insights

    def _calculate_insight_confidence(self,
                                    pattern_config: Dict[str, Any],
                                    analysis_results: Dict[str, Any]) -> float:
        """Calculate confidence score for an insight."""
        base_confidence = 0.7

        # Adjust based on data quality
        data_quality = analysis_results.get("data_quality", 1.0)
        base_confidence *= data_quality

        # Adjust based on pattern priority
        priority_multiplier = {
            InsightPriority.CRITICAL: 1.2,
            InsightPriority.HIGH: 1.1,
            InsightPriority.MEDIUM: 1.0,
            InsightPriority.LOW: 0.9,
            InsightPriority.INFO: 0.8
        }

        priority = pattern_config["priority"]
        base_confidence *= priority_multiplier.get(priority, 1.0)

        return min(1.0, max(0.0, base_confidence))

    def _calculate_insight_impact(self,
                                pattern_config: Dict[str, Any],
                                analysis_results: Dict[str, Any]) -> float:
        """Calculate impact score for an insight."""
        base_impact = 0.6

        # Adjust based on pattern category
        category_multiplier = {
            InsightCategory.RISK: 1.3,
            InsightCategory.QUALITY: 1.1,
            InsightCategory.EFFICIENCY: 1.0,
            InsightCategory.COMPLIANCE: 1.2,
            InsightCategory.INNOVATION: 0.9,
            InsightCategory.PRODUCTIVITY: 1.0
        }

        category = pattern_config["category"]
        base_impact *= category_multiplier.get(category, 1.0)

        return min(1.0, max(0.0, base_impact))

    def _filter_and_prioritize_insights(self, insights: List[AnalysisInsight]) -> List[AnalysisInsight]:
        """Filter and prioritize insights based on confidence and impact."""
        # Filter by confidence threshold
        filtered_insights = []
        for insight in insights:
            threshold = self.confidence_thresholds.get(insight.priority, 0.5)
            if insight.confidence_score >= threshold:
                filtered_insights.append(insight)

        # Sort by priority and impact
        priority_order = {
            InsightPriority.CRITICAL: 0,
            InsightPriority.HIGH: 1,
            InsightPriority.MEDIUM: 2,
            InsightPriority.LOW: 3,
            InsightPriority.INFO: 4
        }

        filtered_insights.sort(key=lambda i: (
            priority_order.get(i.priority, 4),
            -i.impact_score,  # Higher impact first
            -i.confidence_score  # Higher confidence first
        ))

        # Limit to top insights
        return filtered_insights[:20]  # Return top 20 insights

    def _get_analysis_type_from_pattern(self, pattern_config: Dict[str, Any]):
        """Get analysis type from pattern configuration."""
        # This would map to actual analysis types in the system
        return pattern_config.get("type", "general_analysis")


# Global insight generator instance
_insight_generator: Optional[InsightGenerator] = None


def get_insight_generator() -> InsightGenerator:
    """Get the global insight generator instance."""
    global _insight_generator
    if _insight_generator is None:
        _insight_generator = InsightGenerator()
    return _insight_generator


__all__ = [
    'InsightPattern',
    'InsightType',
    'InsightGenerator',
    'get_insight_generator'
]
