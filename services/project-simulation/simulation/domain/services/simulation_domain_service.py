"""Simulation Domain Service - Cross-Aggregate Business Logic.

This module implements domain services that handle cross-aggregate business logic
following Domain-Driven Design (DDD) principles. Domain services encapsulate
business rules and operations that don't naturally belong to a single aggregate.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.domain.entities.project import Project
from simulation.domain.entities.timeline import Timeline
from simulation.domain.entities.team import Team, TeamMemberEntity, TeamRole
from simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, ProjectStatus,
    SimulationStatus
)
from simulation.domain.events import (
    SimulationStarted, SimulationCompleted, ProjectPhaseCompleted,
    ProjectCreated, ProjectStatusChanged, DocumentGenerated
)
from typing import Any, Dict, List

# Define TimelineEvent as a simple type alias for now
TimelineEvent = Dict[str, Any]


class SimulationDomainService:
    """Domain service for simulation business logic across aggregates."""

    def __init__(self):
        """Initialize the simulation domain service."""
        self.logger = get_simulation_logger()

    def validate_simulation_feasibility(self,
                                      project: Project,
                                      timeline: Timeline,
                                      team: Team) -> Tuple[bool, List[str]]:
        """Validate if a simulation is feasible given project, timeline, and team constraints.

        Args:
            project: The project aggregate
            timeline: The timeline aggregate
            team: The team aggregate

        Returns:
            Tuple of (is_feasible, list_of_issues)
        """
        issues = []

        # Validate team capacity vs project requirements
        team_capacity_score = self._calculate_team_capacity_score(team, project)
        if team_capacity_score < 0.6:
            issues.append(".1f")

        # Validate timeline realism
        timeline_realism_score = self._calculate_timeline_realism_score(timeline, project)
        if timeline_realism_score < 0.7:
            issues.append(".1f")

        # Validate project complexity vs team expertise
        complexity_alignment_score = self._calculate_complexity_alignment_score(project, team)
        if complexity_alignment_score < 0.5:
            issues.append(".1f")

        # Validate resource availability
        resource_availability_score = self._calculate_resource_availability_score(team, timeline)
        if resource_availability_score < 0.8:
            issues.append(".1f")

        # Overall feasibility assessment
        is_feasible = len(issues) <= 1  # Allow one minor issue

        if is_feasible:
            self.logger.info(
                "Simulation feasibility validated successfully",
                project_id=project.project_id,
                team_size=len(team.members),
                timeline_phases=len(timeline.phases)
            )
        else:
            self.logger.warning(
                "Simulation feasibility validation failed",
                project_id=project.project_id,
                issues_count=len(issues),
                issues=issues
            )

        return is_feasible, issues

    def calculate_simulation_progress(self,
                                    timeline: Timeline,
                                    completed_events: List[TimelineEvent]) -> Dict[str, Any]:
        """Calculate comprehensive simulation progress metrics.

        Args:
            timeline: The timeline aggregate
            completed_events: List of completed timeline events

        Returns:
            Dictionary with progress metrics
        """
        total_events = len(timeline.events)
        completed_count = len(completed_events)

        # Calculate basic progress
        progress_percentage = (completed_count / total_events) * 100 if total_events > 0 else 0

        # Calculate phase-wise progress
        phase_progress = {}
        for phase in timeline.phases:
            phase_events = [e for e in timeline.events if e.phase_id == phase.phase_id]
            completed_phase_events = [e for e in completed_events if e.phase_id == phase.phase_id]

            phase_progress[phase.phase_id] = {
                "phase_name": phase.name,
                "total_events": len(phase_events),
                "completed_events": len(completed_phase_events),
                "progress_percentage": (len(completed_phase_events) / len(phase_events) * 100) if phase_events else 0,
                "status": phase.status.value
            }

        # Calculate time-based progress
        time_progress = self._calculate_time_based_progress(timeline)

        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(completed_events)

        return {
            "overall_progress": {
                "percentage": progress_percentage,
                "completed_events": completed_count,
                "total_events": total_events,
                "remaining_events": total_events - completed_count
            },
            "phase_progress": phase_progress,
            "time_progress": time_progress,
            "quality_metrics": quality_metrics,
            "estimated_completion": self._estimate_completion_time(timeline, completed_events)
        }

    def optimize_team_assignment(self,
                               project: Project,
                               team: Team,
                               timeline: Timeline) -> Dict[str, Any]:
        """Optimize team member assignments based on project requirements and timeline.

        Args:
            project: The project aggregate
            team: The team aggregate
            timeline: The timeline aggregate

        Returns:
            Dictionary with optimization recommendations
        """
        recommendations = {
            "reassignments": [],
            "additional_hiring": [],
            "skill_gaps": [],
            "workload_balance": {}
        }

        # Analyze current team composition
        current_skills = self._analyze_team_skills(team)
        required_skills = self._analyze_project_skill_requirements(project)

        # Identify skill gaps
        skill_gaps = self._identify_skill_gaps(current_skills, required_skills)
        recommendations["skill_gaps"] = skill_gaps

        # Analyze workload distribution
        workload_analysis = self._analyze_workload_distribution(team, timeline)
        recommendations["workload_balance"] = workload_analysis

        # Generate reassignments if needed
        if skill_gaps:
            reassignments = self._generate_reassignment_recommendations(team, skill_gaps)
            recommendations["reassignments"] = reassignments

        # Recommend additional hiring if gaps are critical
        hiring_needs = self._calculate_hiring_needs(skill_gaps, project)
        recommendations["additional_hiring"] = hiring_needs

        self.logger.info(
            "Team optimization analysis completed",
            project_id=project.project_id,
            skill_gaps_count=len(skill_gaps),
            reassignments_count=len(reassignments),
            hiring_recommendations=len(hiring_needs)
        )

        return recommendations

    def assess_project_risks(self,
                           project: Project,
                           team: Team,
                           timeline: Timeline) -> Dict[str, Any]:
        """Assess project risks and provide mitigation strategies.

        Args:
            project: The project aggregate
            team: The team aggregate
            timeline: The timeline aggregate

        Returns:
            Dictionary with risk assessment and mitigation strategies
        """
        risks = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "mitigation_strategies": [],
            "overall_risk_score": 0.0
        }

        # Technical complexity risks
        complexity_risks = self._assess_complexity_risks(project)
        risks["high_risk"].extend(complexity_risks["high"])
        risks["medium_risk"].extend(complexity_risks["medium"])

        # Team capability risks
        team_risks = self._assess_team_risks(project, team)
        risks["high_risk"].extend(team_risks["high"])
        risks["medium_risk"].extend(team_risks["medium"])

        # Timeline risks
        timeline_risks = self._assess_timeline_risks(timeline, team)
        risks["high_risk"].extend(timeline_risks["high"])
        risks["medium_risk"].extend(timeline_risks["medium"])
        risks["low_risk"].extend(timeline_risks["low"])

        # External dependency risks
        dependency_risks = self._assess_dependency_risks(project)
        risks["medium_risk"].extend(dependency_risks["medium"])
        risks["low_risk"].extend(dependency_risks["low"])

        # Calculate overall risk score
        total_risks = len(risks["high_risk"]) + len(risks["medium_risk"]) + len(risks["low_risk"])
        risk_score = (len(risks["high_risk"]) * 3 + len(risks["medium_risk"]) * 2 + len(risks["low_risk"])) / max(total_risks, 1)
        risks["overall_risk_score"] = min(risk_score, 5.0)  # Cap at 5.0

        # Generate mitigation strategies
        risks["mitigation_strategies"] = self._generate_mitigation_strategies(risks)

        self.logger.info(
            "Project risk assessment completed",
            project_id=project.project_id,
            high_risks=len(risks["high_risk"]),
            medium_risks=len(risks["medium_risk"]),
            overall_risk_score=risks["overall_risk_score"]
        )

        return risks

    def generate_simulation_insights(self,
                                   project: Project,
                                   timeline: Timeline,
                                   team: Team,
                                   events: List[TimelineEvent]) -> Dict[str, Any]:
        """Generate intelligent insights about the simulation progress and outcomes.

        Args:
            project: The project aggregate
            timeline: The timeline aggregate
            team: The team aggregate
            events: List of timeline events

        Returns:
            Dictionary with simulation insights and recommendations
        """
        insights = {
            "performance_insights": [],
            "bottleneck_analysis": [],
            "team_effectiveness": {},
            "timeline_efficiency": {},
            "recommendations": [],
            "predictive_analysis": {}
        }

        # Analyze team performance patterns
        team_performance = self._analyze_team_performance(team, events)
        insights["team_effectiveness"] = team_performance

        # Analyze timeline efficiency
        timeline_efficiency = self._analyze_timeline_efficiency(timeline, events)
        insights["timeline_efficiency"] = timeline_efficiency

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(timeline, events, team)
        insights["bottleneck_analysis"] = bottlenecks

        # Generate performance insights
        performance_insights = self._generate_performance_insights(project, timeline, team, events)
        insights["performance_insights"] = performance_insights

        # Predictive analysis for remaining work
        predictive = self._generate_predictive_analysis(timeline, events)
        insights["predictive_analysis"] = predictive

        # Generate actionable recommendations
        recommendations = self._generate_actionable_recommendations(insights)
        insights["recommendations"] = recommendations

        return insights

    # Private helper methods

    def _calculate_team_capacity_score(self, team: Team, project: Project) -> float:
        """Calculate team capacity score based on project requirements."""
        # Simplified calculation - in real implementation would be more sophisticated
        team_size = len(team.members)
        project_complexity_factor = {"simple": 1.0, "medium": 1.5, "complex": 2.0}[project.complexity.value]

        base_capacity = team_size * 10  # Assume 10 units per team member
        required_capacity = project_complexity_factor * 50  # Base requirement

        capacity_ratio = base_capacity / required_capacity
        return min(max(capacity_ratio, 0.0), 2.0)  # Cap between 0 and 2

    def _calculate_timeline_realism_score(self, timeline: Timeline, project: Project) -> float:
        """Calculate timeline realism score."""
        # Simplified calculation based on phase durations and project complexity
        total_duration_days = sum(phase.duration_days for phase in timeline.phases)
        complexity_factor = {"simple": 1.0, "medium": 1.2, "complex": 1.5}[project.complexity.value]

        expected_duration = project.duration_weeks * 7 * complexity_factor
        realism_ratio = expected_duration / total_duration_days if total_duration_days > 0 else 0

        return min(max(realism_ratio, 0.0), 2.0)

    def _calculate_complexity_alignment_score(self, project: Project, team: Team) -> float:
        """Calculate how well team expertise aligns with project complexity."""
        # Simplified calculation
        team_experience_score = sum(member.experience_years for member in team.members) / len(team.members)
        complexity_requirement = {"simple": 2, "medium": 4, "complex": 6}[project.complexity.value]

        alignment_ratio = team_experience_score / complexity_requirement
        return min(max(alignment_ratio, 0.0), 2.0)

    def _calculate_resource_availability_score(self, team: Team, timeline: Timeline) -> float:
        """Calculate resource availability score."""
        # Simplified calculation based on team size vs timeline demands
        team_capacity = len(team.members) * 8  # 8 hours per day per member
        timeline_demand = sum(phase.duration_days * 8 for phase in timeline.phases)

        availability_ratio = team_capacity / timeline_demand if timeline_demand > 0 else 1.0
        return min(max(availability_ratio, 0.0), 2.0)

    def _calculate_time_based_progress(self, timeline: Timeline) -> Dict[str, Any]:
        """Calculate time-based progress metrics."""
        now = datetime.now()
        total_duration = sum((phase.end_date - phase.start_date).days for phase in timeline.phases)
        elapsed_duration = sum((min(now, phase.end_date) - phase.start_date).days
                             for phase in timeline.phases if now >= phase.start_date)

        time_progress_percentage = (elapsed_duration / total_duration * 100) if total_duration > 0 else 0

        return {
            "elapsed_days": elapsed_duration,
            "total_days": total_duration,
            "time_progress_percentage": time_progress_percentage,
            "is_ahead": time_progress_percentage > 50,  # Simplified ahead/behind calculation
            "is_behind": time_progress_percentage < 30
        }

    def _calculate_quality_metrics(self, completed_events: List[TimelineEvent]) -> Dict[str, Any]:
        """Calculate quality metrics from completed events."""
        if not completed_events:
            return {"average_quality": 0.0, "quality_distribution": {}, "defect_rate": 0.0}

        # Simplified quality calculation
        quality_scores = [event.quality_score for event in completed_events if hasattr(event, 'quality_score')]
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.8

        # Quality distribution
        distribution = {"excellent": 0, "good": 0, "average": 0, "poor": 0}
        for score in quality_scores:
            if score >= 0.9:
                distribution["excellent"] += 1
            elif score >= 0.7:
                distribution["good"] += 1
            elif score >= 0.5:
                distribution["average"] += 1
            else:
                distribution["poor"] += 1

        defect_rate = distribution["poor"] / len(quality_scores) if quality_scores else 0.0

        return {
            "average_quality": average_quality,
            "quality_distribution": distribution,
            "defect_rate": defect_rate,
            "quality_trend": "improving" if average_quality > 0.8 else "stable"
        }

    def _estimate_completion_time(self, timeline: Timeline, completed_events: List[TimelineEvent]) -> datetime:
        """Estimate completion time based on current progress."""
        remaining_events = len(timeline.events) - len(completed_events)
        avg_events_per_day = len(completed_events) / max((datetime.now() - timeline.start_date).days, 1)

        if avg_events_per_day > 0:
            remaining_days = remaining_events / avg_events_per_day
            return datetime.now() + timedelta(days=remaining_days)
        else:
            return timeline.end_date

    def _analyze_team_skills(self, team: Team) -> Dict[str, float]:
        """Analyze team's skill distribution."""
        skills = {}
        for member in team.members:
            for skill, level in member.skills.items():
                if skill not in skills:
                    skills[skill] = []
                skills[skill].append(level)

        # Average skill levels
        return {skill: sum(levels) / len(levels) for skill, levels in skills.items()}

    def _analyze_project_skill_requirements(self, project: Project) -> Dict[str, float]:
        """Analyze project skill requirements."""
        # Simplified skill requirements based on project type and complexity
        base_requirements = {
            "web_application": {"frontend": 3, "backend": 3, "database": 2, "testing": 2},
            "api_service": {"backend": 4, "database": 3, "testing": 3, "security": 2},
            "mobile_application": {"mobile": 4, "backend": 2, "ui_ux": 2, "testing": 2},
            "data_science": {"python": 4, "statistics": 3, "machine_learning": 3, "data_viz": 2},
            "devops_tool": {"infrastructure": 4, "automation": 3, "security": 3, "monitoring": 2}
        }

        requirements = base_requirements.get(project.project_type.value, {})
        complexity_multiplier = {"simple": 1.0, "medium": 1.2, "complex": 1.5}[project.complexity.value]

        return {skill: level * complexity_multiplier for skill, level in requirements.items()}

    def _identify_skill_gaps(self, current_skills: Dict[str, float], required_skills: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify skill gaps in the team."""
        gaps = []
        for skill, required_level in required_skills.items():
            current_level = current_skills.get(skill, 0)
            if current_level < required_level:
                gap_size = required_level - current_level
                severity = "critical" if gap_size > 2 else "moderate" if gap_size > 1 else "minor"
                gaps.append({
                    "skill": skill,
                    "required_level": required_level,
                    "current_level": current_level,
                    "gap_size": gap_size,
                    "severity": severity
                })

        return sorted(gaps, key=lambda x: x["gap_size"], reverse=True)

    def _analyze_workload_distribution(self, team: Team, timeline: Timeline) -> Dict[str, Any]:
        """Analyze workload distribution across team members."""
        # Simplified workload analysis
        member_workloads = {member.member_id: 0 for member in team.members}

        # Distribute timeline events across team members
        for i, event in enumerate(timeline.events):
            member_id = team.members[i % len(team.members)].member_id
            member_workloads[member_id] += 1

        avg_workload = sum(member_workloads.values()) / len(member_workloads)
        max_workload = max(member_workloads.values())
        min_workload = min(member_workloads.values())

        return {
            "average_workload": avg_workload,
            "max_workload": max_workload,
            "min_workload": min_workload,
            "workload_variance": max_workload - min_workload,
            "is_balanced": (max_workload - min_workload) / avg_workload < 0.5
        }

    def _generate_reassignment_recommendations(self, team: Team, skill_gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate team reassignment recommendations."""
        recommendations = []

        for gap in skill_gaps:
            # Find team members with the required skill
            candidates = [
                member for member in team.members
                if gap["skill"] in member.skills and member.skills[gap["skill"]] >= gap["required_level"]
            ]

            if candidates:
                recommendations.append({
                    "skill_gap": gap["skill"],
                    "recommended_member": candidates[0].name,
                    "rationale": f"Has required skill level {candidates[0].skills[gap['skill']]}"
                })

        return recommendations

    def _calculate_hiring_needs(self, skill_gaps: List[Dict[str, Any]], project: Project) -> List[Dict[str, Any]]:
        """Calculate hiring needs based on skill gaps."""
        hiring_needs = []

        critical_gaps = [gap for gap in skill_gaps if gap["severity"] == "critical"]
        for gap in critical_gaps:
            hiring_needs.append({
                "skill": gap["skill"],
                "required_level": gap["required_level"],
                "priority": "high",
                "timeline": "immediate",
                "justification": f"Critical gap of {gap['gap_size']:.1f} in {gap['skill']} skill"
            })

        return hiring_needs

    def _assess_complexity_risks(self, project: Project) -> Dict[str, List[str]]:
        """Assess project complexity risks."""
        risks = {"high": [], "medium": [], "low": []}

        if project.complexity == ComplexityLevel.COMPLEX:
            risks["high"].append("High technical complexity may cause delays")
            risks["medium"].append("Complex requirements may lead to scope creep")

        if project.project_type == ProjectType.DATA_SCIENCE:
            risks["medium"].append("Data science projects have higher uncertainty")
            risks["low"].append("May require specialized expertise")

        return risks

    def _assess_team_risks(self, project: Project, team: Team) -> Dict[str, List[str]]:
        """Assess team-related risks."""
        risks = {"high": [], "medium": [], "low": []}

        if len(team.members) < 3:
            risks["high"].append("Team too small for project scope")

        # Check for key roles
        roles = {member.role for member in team.members}
        required_roles = {TeamRole.DEVELOPER, TeamRole.QA}

        missing_roles = required_roles - roles
        if missing_roles:
            risks["medium"].append(f"Missing key roles: {', '.join(r.value for r in missing_roles)}")

        return risks

    def _assess_timeline_risks(self, timeline: Timeline, team: Team) -> Dict[str, List[str]]:
        """Assess timeline-related risks."""
        risks = {"high": [], "medium": [], "low": []}

        total_duration = sum(phase.duration_days for phase in timeline.phases)
        if total_duration > team.get_team_capacity_days():
            risks["high"].append("Timeline exceeds team capacity")

        # Check for overlapping phases
        phase_dates = [(phase.start_date, phase.end_date) for phase in timeline.phases]
        for i, (start1, end1) in enumerate(phase_dates):
            for j, (start2, end2) in enumerate(phase_dates[i+1:], i+1):
                if (start1 <= start2 <= end1) or (start2 <= start1 <= end2):
                    risks["medium"].append(f"Phase overlap detected between phases {i+1} and {j+1}")

        return risks

    def _assess_dependency_risks(self, project: Project) -> Dict[str, List[str]]:
        """Assess external dependency risks."""
        risks = {"high": [], "medium": [], "low": []}

        # Simplified dependency assessment
        if project.project_type in [ProjectType.WEB_APPLICATION, ProjectType.MOBILE_APPLICATION]:
            risks["medium"].append("External API dependencies may cause integration issues")
            risks["low"].append("Third-party library updates may require refactoring")

        return risks

    def _generate_mitigation_strategies(self, risks: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Generate mitigation strategies for identified risks."""
        strategies = []

        for risk in risks["high"]:
            if "complexity" in risk.lower():
                strategies.append({
                    "risk": risk,
                    "strategy": "Break down complex tasks into smaller, manageable units",
                    "actions": ["Create detailed technical specifications", "Implement agile development practices"],
                    "timeline": "immediate",
                    "owner": "technical_lead"
                })
            elif "team" in risk.lower():
                strategies.append({
                    "risk": risk,
                    "strategy": "Augment team with experienced contractors or consultants",
                    "actions": ["Identify hiring needs", "Start recruitment process"],
                    "timeline": "2_weeks",
                    "owner": "project_manager"
                })

        return strategies

    def _analyze_team_performance(self, team: Team, events: List[TimelineEvent]) -> Dict[str, Any]:
        """Analyze team performance patterns."""
        member_performance = {}

        for member in team.members:
            member_events = [e for e in events if e.assigned_to == member.member_id]
            completed_events = [e for e in member_events if e.status == "completed"]

            if member_events:
                completion_rate = len(completed_events) / len(member_events)
                avg_quality = sum(e.quality_score for e in completed_events if hasattr(e, 'quality_score')) / len(completed_events) if completed_events else 0

                member_performance[member.name] = {
                    "completion_rate": completion_rate,
                    "average_quality": avg_quality,
                    "total_events": len(member_events),
                    "completed_events": len(completed_events)
                }

        return member_performance

    def _analyze_timeline_efficiency(self, timeline: Timeline, events: List[TimelineEvent]) -> Dict[str, Any]:
        """Analyze timeline efficiency metrics."""
        phase_efficiency = {}

        for phase in timeline.phases:
            phase_events = [e for e in timeline.events if e.phase_id == phase.phase_id]
            completed_events = [e for e in events if e.phase_id == phase.phase_id and e.status == "completed"]

            if phase_events:
                planned_duration = (phase.end_date - phase.start_date).days
                actual_completion_time = len(completed_events) * 2  # Assume 2 days per event
                efficiency = planned_duration / actual_completion_time if actual_completion_time > 0 else 0

                phase_efficiency[phase.name] = {
                    "planned_duration": planned_duration,
                    "actual_duration": actual_completion_time,
                    "efficiency": efficiency,
                    "is_on_track": efficiency >= 0.8
                }

        return phase_efficiency

    def _identify_bottlenecks(self, timeline: Timeline, events: List[TimelineEvent], team: Team) -> List[Dict[str, Any]]:
        """Identify bottlenecks in the simulation process."""
        bottlenecks = []

        # Check for phase delays
        for phase in timeline.phases:
            phase_events = [e for e in timeline.events if e.phase_id == phase.phase_id]
            completed_count = len([e for e in events if e.phase_id == phase.phase_id and e.status == "completed"])

            if phase_events and completed_count / len(phase_events) < 0.5:
                bottlenecks.append({
                    "type": "phase_delay",
                    "phase": phase.name,
                    "severity": "high",
                    "description": f"Phase {phase.name} is significantly behind schedule"
                })

        # Check for team member overload
        member_workloads = {}
        for event in events:
            if event.assigned_to:
                member_workloads[event.assigned_to] = member_workloads.get(event.assigned_to, 0) + 1

        avg_workload = sum(member_workloads.values()) / len(member_workloads) if member_workloads else 0
        for member_id, workload in member_workloads.items():
            if workload > avg_workload * 1.5:
                member = next((m for m in team.members if m.member_id == member_id), None)
                if member:
                    bottlenecks.append({
                        "type": "workload_imbalance",
                        "member": member.name,
                        "severity": "medium",
                        "description": f"{member.name} has {workload} events vs team average of {avg_workload:.1f}"
                    })

        return bottlenecks

    def _generate_performance_insights(self, project: Project, timeline: Timeline, team: Team, events: List[TimelineEvent]) -> List[str]:
        """Generate performance insights."""
        insights = []

        # Progress insights
        total_events = len(timeline.events)
        completed_events = len([e for e in events if e.status == "completed"])
        progress_rate = completed_events / total_events if total_events > 0 else 0

        if progress_rate > 0.8:
            insights.append("Project is ahead of schedule with excellent progress")
        elif progress_rate > 0.6:
            insights.append("Project is progressing well within expected timeline")
        else:
            insights.append("Project progress needs improvement to meet timeline goals")

        # Team insights
        if len(team.members) >= 5:
            insights.append("Team size is optimal for project complexity")
        elif len(team.members) < 3:
            insights.append("Consider augmenting team size for better velocity")

        # Quality insights
        quality_scores = [e.quality_score for e in events if hasattr(e, 'quality_score')]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            if avg_quality > 0.85:
                insights.append("Exceptional quality standards are being maintained")
            elif avg_quality > 0.7:
                insights.append("Quality standards are acceptable but could be improved")

        return insights

    def _generate_predictive_analysis(self, timeline: Timeline, events: List[TimelineEvent]) -> Dict[str, Any]:
        """Generate predictive analysis for remaining work."""
        completed_count = len([e for e in events if e.status == "completed"])
        remaining_count = len(timeline.events) - completed_count

        # Simple velocity calculation
        recent_events = sorted(events, key=lambda x: x.completed_at or datetime.min, reverse=True)[:10]
        if recent_events:
            days_span = (recent_events[0].completed_at - recent_events[-1].completed_at).days if recent_events[-1].completed_at else 1
            velocity = len(recent_events) / max(days_span, 1)
            estimated_days_remaining = remaining_count / velocity if velocity > 0 else 30
        else:
            estimated_days_remaining = 30  # Default estimate

        confidence_level = "high" if len(recent_events) >= 5 else "medium" if len(recent_events) >= 3 else "low"

        return {
            "estimated_completion_days": estimated_days_remaining,
            "velocity_events_per_day": velocity if 'velocity' in locals() else 0,
            "confidence_level": confidence_level,
            "risk_factors": ["low_velocity"] if velocity < 1 else []
        }

    def _generate_actionable_recommendations(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on insights."""
        recommendations = []

        # Based on bottlenecks
        for bottleneck in insights.get("bottleneck_analysis", []):
            if bottleneck["type"] == "phase_delay":
                recommendations.append({
                    "category": "timeline",
                    "priority": "high",
                    "action": f"Allocate additional resources to {bottleneck['phase']} phase",
                    "expected_impact": "Reduce phase delay by 30-50%"
                })
            elif bottleneck["type"] == "workload_imbalance":
                recommendations.append({
                    "category": "team",
                    "priority": "medium",
                    "action": f"Rebalance workload for {bottleneck['member']}",
                    "expected_impact": "Improve team efficiency by 20%"
                })

        # Based on team effectiveness
        team_effectiveness = insights.get("team_effectiveness", {})
        low_performers = [name for name, perf in team_effectiveness.items() if perf.get("completion_rate", 0) < 0.7]
        if low_performers:
            recommendations.append({
                "category": "team",
                "priority": "medium",
                "action": f"Provide additional support to team members: {', '.join(low_performers)}",
                "expected_impact": "Improve completion rates by 25%"
            })

        return recommendations


# Global domain service instance
_simulation_domain_service: Optional[SimulationDomainService] = None


def get_simulation_domain_service() -> SimulationDomainService:
    """Get the global simulation domain service instance."""
    global _simulation_domain_service
    if _simulation_domain_service is None:
        _simulation_domain_service = SimulationDomainService()
    return _simulation_domain_service


__all__ = [
    'SimulationDomainService',
    'get_simulation_domain_service'
]
