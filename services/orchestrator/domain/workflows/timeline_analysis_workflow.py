"""
Timeline Analysis Workflow - Phase 2 Day 4
Part of Enhanced Roadmap v2.0 - Workflow C: Timeline Analysis

This workflow analyzes project timelines using historical data and velocity predictions.
Integrates with Project Simulation and Analysis services.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field

import httpx


@dataclass
class TimelineEstimate:
    """Timeline estimation for a feature or project."""
    feature_id: str
    estimated_duration_days: int
    estimated_sprints: int
    confidence_level: float  # 0.0 - 1.0
    best_case_days: int
    worst_case_days: int
    most_likely_days: int
    velocity_used: float  # Story points per sprint
    sprint_duration_weeks: int = 2
    buffer_percentage: float = 0.2  # 20% buffer by default


@dataclass
class HistoricalTrend:
    """Historical trend data for timeline predictions."""
    metric_name: str  # e.g., "velocity", "completion_rate", "defect_rate"
    historical_values: List[float]
    trend_direction: str  # "increasing", "decreasing", "stable"
    average_value: float
    std_deviation: float
    confidence: float  # 0.0 - 1.0


@dataclass
class TimelineAnalysisResult:
    """Complete timeline analysis result from Workflow C."""
    workflow_id: str
    feature_breakdown: Dict[str, Any]  # From Workflow A
    timeline_estimates: List[TimelineEstimate]
    historical_trends: List[HistoricalTrend]
    velocity_forecast: Dict[str, float]  # Sprint -> predicted velocity
    risk_factors: List[str]
    recommendations: List[str]
    overall_confidence: float  # 0.0 - 1.0
    estimated_completion_date: date
    created_at: datetime = field(default_factory=datetime.utcnow)


class TimelineAnalysisWorkflow:
    """
    Workflow C: Timeline Analysis
    
    Analyzes project timelines using:
    - Historical velocity data
    - Team capacity trends
    - Complexity analysis
    - Risk assessment
    
    Integrates with:
    - Project Simulation service (historical analysis)
    - Analysis Service (trend analysis)
    - User Store (velocity data)
    
    Part of Enhanced Roadmap v2.0 Phase 2 implementation.
    """
    
    def __init__(
        self,
        project_simulation_url: str = "http://project-simulation:5075",
        analysis_service_url: str = "http://analysis-service:8004",
        user_store_url: str = "http://user-store:5130",
        workflow_logger = None
    ):
        """
        Initialize Workflow C with service URLs.
        
        Args:
            project_simulation_url: URL for Project Simulation service
            analysis_service_url: URL for Analysis Service
            user_store_url: URL for User Store service
            workflow_logger: WorkflowLogger instance for logging
        """
        self.project_simulation_url = project_simulation_url
        self.analysis_service_url = analysis_service_url
        self.user_store_url = user_store_url
        self.workflow_logger = workflow_logger
        self.timeout = 30.0
        
    async def execute(
        self,
        feature_breakdown: Dict[str, Any],
        team_id: str,
        historical_context: Optional[Dict[str, Any]] = None,
        parent_workflow_id: Optional[str] = None
    ) -> TimelineAnalysisResult:
        """
        Execute Workflow C: Timeline Analysis.
        
        Args:
            feature_breakdown: Feature breakdown from Workflow A
            team_id: Team identifier for velocity data
            historical_context: Historical context from Workflow B
            parent_workflow_id: Parent workflow ID for tracing
            
        Returns:
            TimelineAnalysisResult with complete timeline analysis
        """
        # Generate workflow ID
        workflow_id = f"workflow_c_{str(uuid.uuid4())[:8]}"
        
        # Log workflow start
        if self.workflow_logger:
            await self.workflow_logger.log_workflow_start(
                workflow_id=workflow_id,
                operation="timeline_analysis_workflow_c",
                context={
                    "feature_breakdown": bool(feature_breakdown),
                    "team_id": team_id,
                    "parent_workflow": parent_workflow_id
                }
            )
        
        try:
            # Step 1: Get team velocity data
            velocity_data = await self._get_team_velocity(
                team_id=team_id,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="team_velocity_retrieved",
                    step_data={
                        "team_id": team_id,
                        "average_velocity": velocity_data.get("average_velocity", 0)
                    }
                )
            
            # Step 2: Analyze historical trends
            historical_trends = await self._analyze_historical_trends(
                team_id=team_id,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="historical_trends_analyzed",
                    step_data={
                        "trends_count": len(historical_trends)
                    }
                )
            
            # Step 3: Calculate timeline estimates
            timeline_estimates = await self._calculate_timeline_estimates(
                feature_breakdown=feature_breakdown,
                velocity_data=velocity_data,
                historical_trends=historical_trends,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="timeline_estimates_calculated",
                    step_data={
                        "estimates_count": len(timeline_estimates)
                    }
                )
            
            # Step 4: Generate velocity forecast
            velocity_forecast = await self._generate_velocity_forecast(
                velocity_data=velocity_data,
                historical_trends=historical_trends,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="velocity_forecast_generated",
                    step_data={
                        "forecast_sprints": len(velocity_forecast)
                    }
                )
            
            # Step 5: Identify risk factors
            risk_factors = self._identify_timeline_risks(
                timeline_estimates=timeline_estimates,
                historical_trends=historical_trends,
                velocity_data=velocity_data
            )
            
            # Step 6: Generate recommendations
            recommendations = self._generate_timeline_recommendations(
                timeline_estimates=timeline_estimates,
                risk_factors=risk_factors,
                velocity_data=velocity_data
            )
            
            # Step 7: Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                timeline_estimates=timeline_estimates,
                historical_trends=historical_trends
            )
            
            # Step 8: Estimate completion date
            estimated_completion_date = self._calculate_completion_date(
                timeline_estimates=timeline_estimates
            )
            
            # Create result
            result = TimelineAnalysisResult(
                workflow_id=workflow_id,
                feature_breakdown=feature_breakdown,
                timeline_estimates=timeline_estimates,
                historical_trends=historical_trends,
                velocity_forecast=velocity_forecast,
                risk_factors=risk_factors,
                recommendations=recommendations,
                overall_confidence=overall_confidence,
                estimated_completion_date=estimated_completion_date
            )
            
            # Log workflow completion
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_complete(
                    workflow_id=workflow_id,
                    duration_ms=0,
                    success=True,
                    result_summary={
                        "timeline_estimates": len(timeline_estimates),
                        "overall_confidence": overall_confidence,
                        "estimated_days": sum(e.estimated_duration_days for e in timeline_estimates),
                        "risk_factors": len(risk_factors)
                    }
                )
            
            return result
            
        except Exception as e:
            # Log error
            if self.workflow_logger:
                await self.workflow_logger.log_error(
                    workflow_id=workflow_id,
                    error=e,
                    context={"stage": "timeline_analysis_workflow_c"}
                )
            raise
    
    async def _get_team_velocity(
        self,
        team_id: str,
        workflow_id: str
    ) -> Dict[str, Any]:
        """Get team velocity data from User Store."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.user_store_url}/api/v1/teams/{team_id}/velocity"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    # Fallback to default velocity
                    return self._get_default_velocity()
                    
        except Exception:
            return self._get_default_velocity()
    
    def _get_default_velocity(self) -> Dict[str, Any]:
        """Default velocity when service is unavailable."""
        return {
            "team_id": "default",
            "average_velocity": 20.0,  # Story points per sprint
            "sprint_duration_weeks": 2,
            "recent_sprints": [
                {"sprint": 1, "velocity": 18.0},
                {"sprint": 2, "velocity": 20.0},
                {"sprint": 3, "velocity": 22.0}
            ],
            "velocity_trend": "increasing"
        }
    
    async def _analyze_historical_trends(
        self,
        team_id: str,
        workflow_id: str
    ) -> List[HistoricalTrend]:
        """Analyze historical trends using Project Simulation service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.project_simulation_url}/api/v1/analyze/trends",
                    json={
                        "team_id": team_id,
                        "metrics": ["velocity", "completion_rate", "cycle_time"],
                        "lookback_days": 90
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    trends = []
                    
                    for trend_data in data.get("trends", []):
                        trends.append(HistoricalTrend(
                            metric_name=trend_data.get("metric", "unknown"),
                            historical_values=trend_data.get("values", []),
                            trend_direction=trend_data.get("direction", "stable"),
                            average_value=trend_data.get("average", 0.0),
                            std_deviation=trend_data.get("std_dev", 0.0),
                            confidence=trend_data.get("confidence", 0.5)
                        ))
                    
                    return trends
                else:
                    return self._get_default_trends()
                    
        except Exception:
            return self._get_default_trends()
    
    def _get_default_trends(self) -> List[HistoricalTrend]:
        """Default trends when service is unavailable."""
        return [
            HistoricalTrend(
                metric_name="velocity",
                historical_values=[18.0, 19.0, 20.0, 21.0, 20.0],
                trend_direction="stable",
                average_value=19.6,
                std_deviation=1.1,
                confidence=0.7
            ),
            HistoricalTrend(
                metric_name="completion_rate",
                historical_values=[0.85, 0.88, 0.90, 0.92, 0.91],
                trend_direction="increasing",
                average_value=0.89,
                std_deviation=0.03,
                confidence=0.8
            )
        ]
    
    async def _calculate_timeline_estimates(
        self,
        feature_breakdown: Dict[str, Any],
        velocity_data: Dict[str, Any],
        historical_trends: List[HistoricalTrend],
        workflow_id: str
    ) -> List[TimelineEstimate]:
        """Calculate timeline estimates for features."""
        estimates = []
        
        # Extract story points from feature breakdown
        total_story_points = feature_breakdown.get("total_story_points", 0)
        if total_story_points == 0:
            # Estimate based on feature count
            total_story_points = len(feature_breakdown.get("user_stories", [])) * 5
        
        # Get velocity
        avg_velocity = velocity_data.get("average_velocity", 20.0)
        sprint_weeks = velocity_data.get("sprint_duration_weeks", 2)
        
        # Calculate estimates
        estimated_sprints = int(total_story_points / avg_velocity) + 1
        estimated_days = estimated_sprints * sprint_weeks * 7
        
        # Calculate confidence based on trend stability
        velocity_trend = next(
            (t for t in historical_trends if t.metric_name == "velocity"),
            None
        )
        confidence = velocity_trend.confidence if velocity_trend else 0.7
        
        # Calculate best/worst case (±20%)
        best_case = int(estimated_days * 0.8)
        worst_case = int(estimated_days * 1.2)
        
        estimate = TimelineEstimate(
            feature_id=feature_breakdown.get("feature_id", "unknown"),
            estimated_duration_days=estimated_days,
            estimated_sprints=estimated_sprints,
            confidence_level=confidence,
            best_case_days=best_case,
            worst_case_days=worst_case,
            most_likely_days=estimated_days,
            velocity_used=avg_velocity,
            sprint_duration_weeks=sprint_weeks
        )
        
        estimates.append(estimate)
        return estimates
    
    async def _generate_velocity_forecast(
        self,
        velocity_data: Dict[str, Any],
        historical_trends: List[HistoricalTrend],
        workflow_id: str
    ) -> Dict[str, float]:
        """Generate velocity forecast for upcoming sprints."""
        forecast = {}
        
        # Get current velocity
        avg_velocity = velocity_data.get("average_velocity", 20.0)
        trend_direction = velocity_data.get("velocity_trend", "stable")
        
        # Project for next 6 sprints
        for sprint in range(1, 7):
            if trend_direction == "increasing":
                # Gradual increase (1% per sprint)
                forecast[f"sprint_{sprint}"] = avg_velocity * (1 + 0.01 * sprint)
            elif trend_direction == "decreasing":
                # Gradual decrease (1% per sprint)
                forecast[f"sprint_{sprint}"] = avg_velocity * (1 - 0.01 * sprint)
            else:
                # Stable
                forecast[f"sprint_{sprint}"] = avg_velocity
        
        return forecast
    
    def _identify_timeline_risks(
        self,
        timeline_estimates: List[TimelineEstimate],
        historical_trends: List[HistoricalTrend],
        velocity_data: Dict[str, Any]
    ) -> List[str]:
        """Identify timeline-related risks."""
        risks = []
        
        # Check for low confidence
        if any(e.confidence_level < 0.6 for e in timeline_estimates):
            risks.append("Low confidence in timeline estimates due to limited historical data")
        
        # Check for long duration
        total_days = sum(e.estimated_duration_days for e in timeline_estimates)
        if total_days > 90:
            risks.append("Long project duration (>90 days) increases uncertainty")
        
        # Check velocity stability
        velocity_trend = next(
            (t for t in historical_trends if t.metric_name == "velocity"),
            None
        )
        if velocity_trend and velocity_trend.std_deviation > 3.0:
            risks.append("High velocity variability may impact timeline predictability")
        
        # Check trend direction
        if velocity_data.get("velocity_trend") == "decreasing":
            risks.append("Decreasing velocity trend may extend timeline")
        
        return risks
    
    def _generate_timeline_recommendations(
        self,
        timeline_estimates: List[TimelineEstimate],
        risk_factors: List[str],
        velocity_data: Dict[str, Any]
    ) -> List[str]:
        """Generate timeline recommendations."""
        recommendations = []
        
        # Based on confidence
        if any(e.confidence_level < 0.7 for e in timeline_estimates):
            recommendations.append("Add 20% buffer time due to uncertainty")
        
        # Based on duration
        total_days = sum(e.estimated_duration_days for e in timeline_estimates)
        if total_days > 60:
            recommendations.append("Consider breaking into smaller milestones")
        
        # Based on velocity trend
        if velocity_data.get("velocity_trend") == "decreasing":
            recommendations.append("Investigate causes of velocity decrease")
        
        # General best practices
        recommendations.append("Review and adjust estimates after first sprint")
        recommendations.append("Monitor velocity weekly for early warning signs")
        
        return recommendations
    
    def _calculate_overall_confidence(
        self,
        timeline_estimates: List[TimelineEstimate],
        historical_trends: List[HistoricalTrend]
    ) -> float:
        """Calculate overall confidence score."""
        if not timeline_estimates:
            return 0.5
        
        # Average of individual confidences
        estimate_confidence = sum(e.confidence_level for e in timeline_estimates) / len(timeline_estimates)
        
        # Factor in trend confidence
        trend_confidences = [t.confidence for t in historical_trends]
        trend_confidence = sum(trend_confidences) / len(trend_confidences) if trend_confidences else 0.5
        
        # Weighted average (70% estimates, 30% trends)
        overall = (estimate_confidence * 0.7) + (trend_confidence * 0.3)
        
        return min(overall, 1.0)
    
    def _calculate_completion_date(
        self,
        timeline_estimates: List[TimelineEstimate]
    ) -> date:
        """Calculate estimated completion date."""
        if not timeline_estimates:
            return date.today()
        
        total_days = sum(e.estimated_duration_days for e in timeline_estimates)
        completion_date = date.today() + timedelta(days=total_days)
        
        return completion_date

