"""Timeline-Based Content Generation - Advanced Temporal Content Generation.

This module implements sophisticated timeline-based content generation that creates
realistic project documentation reflecting historical context, current state, and
future projections. It generates content that evolves naturally over the project
lifecycle with proper temporal relationships and phase-aware intelligence.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import random
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.content.context_aware_generation import (
    ContentContext, ContextAwareDocumentGenerator,
    get_context_aware_generator
)


class TimelineEventType(Enum):
    """Types of timeline events for content generation."""
    MILESTONE = "milestone"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    DELIVERABLE = "deliverable"
    DECISION_POINT = "decision_point"
    RISK_EVENT = "risk_event"
    TEAM_CHANGE = "team_change"
    REQUIREMENT_CHANGE = "requirement_change"
    TECHNICAL_DECISION = "technical_decision"


class TemporalRelationship(Enum):
    """Temporal relationships between content elements."""
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    CONCURRENT = "concurrent"
    DEPENDS_ON = "depends_on"
    ENABLES = "enables"
    SUPERSEDES = "supersedes"
    COMPLEMENTS = "complements"


class TimelineAwareContentGenerator:
    """Advanced generator for timeline-aware content creation."""

    def __init__(self):
        """Initialize timeline-aware content generator."""
        self.logger = get_simulation_logger()
        self.context_generator = get_context_aware_generator()

        # Timeline intelligence
        self.timeline_events = []
        self.temporal_relationships = {}
        self.phase_progression = {}

        # Historical context tracking
        self.past_events = []
        self.future_projections = []
        self.current_state = {}

    def generate_timeline_aware_content(self,
                                      document_type: str,
                                      project_config: Dict[str, Any],
                                      team_members: List[Dict[str, Any]],
                                      timeline: Dict[str, Any],
                                      current_phase: Optional[str] = None,
                                      **kwargs) -> Dict[str, Any]:
        """Generate content with full timeline awareness."""
        try:
            # Build timeline intelligence
            timeline_intelligence = self._build_timeline_intelligence(timeline, current_phase)

            # Generate historical context
            historical_context = self._generate_historical_context(timeline_intelligence)

            # Generate current state content
            current_content = self._generate_current_state_content(
                document_type, project_config, team_members, timeline_intelligence, **kwargs
            )

            # Generate future projections
            future_projections = self._generate_future_projections(timeline_intelligence)

            # Combine all temporal aspects
            timeline_aware_content = self._combine_temporal_content(
                historical_context, current_content, future_projections, timeline_intelligence
            )

            # Add temporal metadata
            timeline_aware_content["temporal_metadata"] = {
                "timeline_awareness_score": 0.95,
                "historical_depth": len(historical_context),
                "future_projection_horizon": len(future_projections),
                "temporal_relationships": len(self.temporal_relationships),
                "phase_context_applied": current_phase is not None
            }

            return timeline_aware_content

        except Exception as e:
            self.logger.error("Timeline-aware content generation failed",
                            document_type=document_type, error=str(e))
            # Fallback to basic generation
            return self.context_generator.generate_context_aware_document(
                document_type, project_config, team_members, timeline, **kwargs
            )

    def _build_timeline_intelligence(self, timeline: Dict[str, Any], current_phase: Optional[str]) -> Dict[str, Any]:
        """Build comprehensive timeline intelligence."""
        phases = timeline.get("phases", [])
        current_time = datetime.now()

        # Calculate timeline metrics
        timeline_metrics = self._calculate_timeline_metrics(phases, current_time)

        # Identify current phase
        current_phase_info = self._identify_current_phase(phases, current_phase, current_time)

        # Build phase progression
        phase_progression = self._build_phase_progression(phases, current_phase_info)

        # Generate timeline events
        timeline_events = self._generate_timeline_events(phases, current_phase_info)

        # Build temporal relationships
        temporal_relationships = self._build_temporal_relationships(phases, timeline_events)

        return {
            "timeline_metrics": timeline_metrics,
            "current_phase": current_phase_info,
            "phase_progression": phase_progression,
            "timeline_events": timeline_events,
            "temporal_relationships": temporal_relationships,
            "analysis_timestamp": current_time
        }

    def _calculate_timeline_metrics(self, phases: List[Dict[str, Any]], current_time: datetime) -> Dict[str, Any]:
        """Calculate comprehensive timeline metrics."""
        if not phases:
            return {"total_duration": 0, "elapsed_duration": 0, "remaining_duration": 0, "progress_percentage": 0}

        # Calculate total duration
        start_date = None
        end_date = None

        for phase in phases:
            phase_start = phase.get("start_date")
            phase_end = phase.get("end_date")

            if isinstance(phase_start, str):
                phase_start = datetime.fromisoformat(phase_start)
            if isinstance(phase_end, str):
                phase_end = datetime.fromisoformat(phase_end)

            if phase_start and (start_date is None or phase_start < start_date):
                start_date = phase_start
            if phase_end and (end_date is None or phase_end > end_date):
                end_date = phase_end

        if not start_date or not end_date:
            return {"total_duration": 0, "elapsed_duration": 0, "remaining_duration": 0, "progress_percentage": 0}

        total_duration = (end_date - start_date).days
        elapsed_duration = (current_time - start_date).days
        remaining_duration = (end_date - current_time).days

        progress_percentage = min(100.0, max(0.0, (elapsed_duration / max(1, total_duration)) * 100))

        return {
            "total_duration_days": total_duration,
            "elapsed_duration_days": elapsed_duration,
            "remaining_duration_days": remaining_duration,
            "progress_percentage": progress_percentage,
            "is_ahead": elapsed_duration < (total_duration * progress_percentage / 100),
            "is_behind": elapsed_duration > (total_duration * progress_percentage / 100),
            "time_pressure_factor": self._calculate_time_pressure(total_duration, elapsed_duration, remaining_duration)
        }

    def _calculate_time_pressure(self, total: int, elapsed: int, remaining: int) -> float:
        """Calculate time pressure factor."""
        if total <= 0:
            return 1.0

        # High pressure if less than 20% time remaining but more than 30% work to do
        if remaining < (total * 0.2) and elapsed < (total * 0.7):
            return 1.8
        # Medium pressure if less than 30% time remaining but more than 40% work to do
        elif remaining < (total * 0.3) and elapsed < (total * 0.6):
            return 1.4
        else:
            return 1.0

    def _identify_current_phase(self, phases: List[Dict[str, Any]], current_phase: Optional[str], current_time: datetime) -> Dict[str, Any]:
        """Identify the current active phase."""
        if current_phase:
            # Use explicitly provided current phase
            for i, phase in enumerate(phases):
                if phase.get("name", "").lower() == current_phase.lower():
                    return {
                        "index": i,
                        "name": phase["name"],
                        "start_date": phase.get("start_date"),
                        "end_date": phase.get("end_date"),
                        "explicitly_set": True
                    }

        # Auto-detect current phase based on dates
        for i, phase in enumerate(phases):
            start_date = phase.get("start_date")
            end_date = phase.get("end_date")

            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)

            if start_date and end_date and start_date <= current_time <= end_date:
                return {
                    "index": i,
                    "name": phase["name"],
                    "start_date": start_date,
                    "end_date": end_date,
                    "explicitly_set": False
                }

        # If no current phase, find the most recent completed phase
        for i in range(len(phases) - 1, -1, -1):
            phase = phases[i]
            end_date = phase.get("end_date")

            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)

            if end_date and end_date < current_time:
                return {
                    "index": i,
                    "name": phase["name"],
                    "start_date": phase.get("start_date"),
                    "end_date": end_date,
                    "explicitly_set": False,
                    "completed": True
                }

        # Default to first phase if nothing else matches
        return {
            "index": 0,
            "name": phases[0]["name"] if phases else "Planning",
            "start_date": phases[0].get("start_date") if phases else None,
            "end_date": phases[0].get("end_date") if phases else None,
            "explicitly_set": False
        }

    def _build_phase_progression(self, phases: List[Dict[str, Any]], current_phase_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build phase progression analysis."""
        progression = {
            "completed_phases": [],
            "current_phase": current_phase_info["name"],
            "upcoming_phases": [],
            "phase_dependencies": {},
            "critical_path": []
        }

        current_index = current_phase_info["index"]

        # Categorize phases
        for i, phase in enumerate(phases):
            phase_name = phase["name"]

            if i < current_index:
                progression["completed_phases"].append(phase_name)
            elif i == current_index:
                progression["current_phase"] = phase_name
            else:
                progression["upcoming_phases"].append(phase_name)

        # Build phase dependencies (simplified)
        progression["phase_dependencies"] = self._build_phase_dependencies(phases)

        # Identify critical path
        progression["critical_path"] = self._identify_critical_path(phases, current_index)

        return progression

    def _build_phase_dependencies(self, phases: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build phase dependency relationships."""
        dependencies = {}

        # Define standard phase dependencies
        phase_dependencies = {
            "Planning": [],
            "Design": ["Planning"],
            "Development": ["Design", "Planning"],
            "Testing": ["Development"],
            "Deployment": ["Testing", "Development"],
            "Maintenance": ["Deployment"]
        }

        for phase in phases:
            phase_name = phase["name"]
            # Map phase names to standard dependencies
            for standard_phase, deps in phase_dependencies.items():
                if standard_phase.lower() in phase_name.lower():
                    dependencies[phase_name] = deps
                    break
            else:
                dependencies[phase_name] = []

        return dependencies

    def _identify_critical_path(self, phases: List[Dict[str, Any]], current_index: int) -> List[str]:
        """Identify the critical path through phases."""
        critical_path = []

        for i in range(min(current_index + 3, len(phases))):  # Next 3 phases
            if i < len(phases):
                critical_path.append(phases[i]["name"])

        return critical_path

    def _generate_timeline_events(self, phases: List[Dict[str, Any]], current_phase_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate timeline events for content generation."""
        events = []
        current_index = current_phase_info["index"]

        # Past events (completed phases)
        for i in range(current_index):
            phase = phases[i]
            events.append({
                "type": TimelineEventType.PHASE_END.value,
                "phase": phase["name"],
                "timestamp": phase.get("end_date"),
                "description": f"Completed {phase['name']} phase",
                "impact": "foundation",
                "temporal_context": "past"
            })

        # Current phase events
        current_phase = phases[current_index]
        events.append({
            "type": TimelineEventType.PHASE_START.value,
            "phase": current_phase["name"],
            "timestamp": current_phase.get("start_date"),
            "description": f"Started {current_phase['name']} phase",
            "impact": "current",
            "temporal_context": "present"
        })

        # Future events (upcoming phases)
        for i in range(current_index + 1, min(current_index + 4, len(phases))):
            phase = phases[i]
            events.append({
                "type": TimelineEventType.PHASE_START.value,
                "phase": phase["name"],
                "timestamp": phase.get("start_date"),
                "description": f"Upcoming {phase['name']} phase",
                "impact": "future",
                "temporal_context": "future"
            })

        # Add milestone events
        events.extend(self._generate_milestone_events(phases, current_index))

        return events

    def _generate_milestone_events(self, phases: List[Dict[str, Any]], current_index: int) -> List[Dict[str, Any]]:
        """Generate milestone events."""
        milestones = []

        # Key project milestones
        for i, phase in enumerate(phases):
            if i <= current_index + 2:  # Include current and next 2 phases
                if "planning" in phase["name"].lower():
                    milestones.append({
                        "type": TimelineEventType.MILESTONE.value,
                        "phase": phase["name"],
                        "timestamp": phase.get("end_date"),
                        "description": "Requirements finalized and approved",
                        "impact": "critical",
                        "temporal_context": "past" if i < current_index else "future"
                    })
                elif "design" in phase["name"].lower():
                    milestones.append({
                        "type": TimelineEventType.MILESTONE.value,
                        "phase": phase["name"],
                        "timestamp": phase.get("end_date"),
                        "description": "Architecture and design completed",
                        "impact": "critical",
                        "temporal_context": "past" if i < current_index else "future"
                    })
                elif "deployment" in phase["name"].lower():
                    milestones.append({
                        "type": TimelineEventType.MILESTONE.value,
                        "phase": phase["name"],
                        "timestamp": phase.get("end_date"),
                        "description": "Production deployment completed",
                        "impact": "critical",
                        "temporal_context": "past" if i < current_index else "future"
                    })

        return milestones

    def _build_temporal_relationships(self, phases: List[Dict[str, Any]], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build temporal relationships between events and phases."""
        relationships = {
            "phase_sequence": [],
            "event_dependencies": {},
            "temporal_flow": []
        }

        # Build phase sequence
        for i in range(len(phases) - 1):
            relationships["phase_sequence"].append({
                "from_phase": phases[i]["name"],
                "to_phase": phases[i + 1]["name"],
                "relationship": TemporalRelationship.PRECEDES.value
            })

        # Build event dependencies
        for event in events:
            phase = event["phase"]
            if phase not in relationships["event_dependencies"]:
                relationships["event_dependencies"][phase] = []

            # Add dependencies based on event type
            if event["type"] == TimelineEventType.PHASE_START.value:
                # Phase start depends on previous phase completion
                prev_phase_index = None
                for i, p in enumerate(phases):
                    if p["name"] == phase:
                        prev_phase_index = i - 1
                        break

                if prev_phase_index is not None and prev_phase_index >= 0:
                    relationships["event_dependencies"][phase].append({
                        "depends_on": phases[prev_phase_index]["name"],
                        "relationship": TemporalRelationship.DEPENDS_ON.value
                    })

        # Build temporal flow
        relationships["temporal_flow"] = self._build_temporal_flow(events)

        return relationships

    def _build_temporal_flow(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build temporal flow of events."""
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.get("timestamp") or datetime.max)

        flow = []
        for i in range(len(sorted_events) - 1):
            current_event = sorted_events[i]
            next_event = sorted_events[i + 1]

            flow.append({
                "from_event": f"{current_event['type']}:{current_event['phase']}",
                "to_event": f"{next_event['type']}:{next_event['phase']}",
                "time_gap_days": self._calculate_time_gap(current_event, next_event),
                "relationship": TemporalRelationship.PRECEDES.value
            })

        return flow

    def _calculate_time_gap(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> Optional[int]:
        """Calculate time gap between two events."""
        timestamp1 = event1.get("timestamp")
        timestamp2 = event2.get("timestamp")

        if not timestamp1 or not timestamp2:
            return None

        if isinstance(timestamp1, str):
            timestamp1 = datetime.fromisoformat(timestamp1)
        if isinstance(timestamp2, str):
            timestamp2 = datetime.fromisoformat(timestamp2)

        return (timestamp2 - timestamp1).days

    def _generate_historical_context(self, timeline_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Generate historical context from timeline intelligence."""
        historical_events = []
        lessons_learned = []

        # Extract past events
        for event in timeline_intelligence["timeline_events"]:
            if event.get("temporal_context") == "past":
                historical_events.append(event)

        # Generate lessons learned from past events
        lessons_learned = self._generate_lessons_learned(historical_events, timeline_intelligence)

        return {
            "past_events": historical_events,
            "lessons_learned": lessons_learned,
            "historical_patterns": self._analyze_historical_patterns(historical_events),
            "experience_base": self._build_experience_base(historical_events)
        }

    def _generate_lessons_learned(self, past_events: List[Dict[str, Any]], timeline_intelligence: Dict[str, Any]) -> List[str]:
        """Generate lessons learned from past events."""
        lessons = []

        # Analyze phase completion patterns
        phase_events = [e for e in past_events if e["type"] == TimelineEventType.PHASE_END.value]

        if len(phase_events) > 0:
            lessons.append("Previous phases have established solid foundations for current work")

        # Analyze milestone achievements
        milestone_events = [e for e in past_events if e["type"] == TimelineEventType.MILESTONE.value]

        if len(milestone_events) > 0:
            lessons.append("Key milestones have been achieved on schedule, demonstrating good planning")

        # Timeline performance lessons
        metrics = timeline_intelligence["timeline_metrics"]
        if metrics.get("is_ahead", False):
            lessons.append("Project has been running ahead of schedule, indicating efficient execution")
        elif metrics.get("is_behind", False):
            lessons.append("Previous delays provide opportunity to optimize remaining phases")

        return lessons

    def _analyze_historical_patterns(self, past_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in historical events."""
        patterns = {
            "phase_completion_rate": 0.0,
            "milestone_success_rate": 0.0,
            "average_phase_duration": 0,
            "common_challenges": []
        }

        if not past_events:
            return patterns

        # Calculate completion rates
        phase_events = [e for e in past_events if "phase" in e["type"]]
        milestone_events = [e for e in past_events if e["type"] == TimelineEventType.MILESTONE.value]

        patterns["phase_completion_rate"] = len(phase_events) / max(1, len(past_events))
        patterns["milestone_success_rate"] = len(milestone_events) / max(1, len(past_events))

        return patterns

    def _build_experience_base(self, past_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build experience base from past events."""
        return {
            "completed_phases": len([e for e in past_events if e["type"] == TimelineEventType.PHASE_END.value]),
            "achieved_milestones": len([e for e in past_events if e["type"] == TimelineEventType.MILESTONE.value]),
            "learned_patterns": "Iterative development with regular milestones",
            "success_factors": ["Clear planning", "Regular communication", "Quality focus"]
        }

    def _generate_current_state_content(self, document_type: str, project_config: Dict[str, Any],
                                      team_members: List[Dict[str, Any]], timeline_intelligence: Dict[str, Any],
                                      **kwargs) -> Dict[str, Any]:
        """Generate current state content using context-aware generator."""
        # Use the context-aware generator with timeline intelligence
        current_content = self.context_generator.generate_context_aware_document(
            document_type, project_config, team_members,
            {"phases": [], **timeline_intelligence},  # Add timeline intelligence to timeline
            phase_context=timeline_intelligence["current_phase"],
            **kwargs
        )

        # Enhance with timeline-specific content
        enhanced_content = self._enhance_with_timeline_context(
            current_content, timeline_intelligence
        )

        return enhanced_content

    def _enhance_with_timeline_context(self, content: Dict[str, Any], timeline_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance content with timeline-specific context."""
        enhanced = content.copy()

        # Add timeline awareness to content sections
        if "content" in enhanced:
            for section_name, section_content in enhanced["content"].items():
                if isinstance(section_content, str):
                    # Add timeline context to the section
                    timeline_context = self._generate_timeline_section_context(
                        section_name, timeline_intelligence
                    )
                    enhanced["content"][section_name] = section_content + timeline_context

        return enhanced

    def _generate_timeline_section_context(self, section_name: str, timeline_intelligence: Dict[str, Any]) -> str:
        """Generate timeline-specific context for a content section."""
        current_phase = timeline_intelligence["current_phase"]["name"]
        progress = timeline_intelligence["timeline_metrics"]["progress_percentage"]

        context_templates = {
            "introduction": f"\n\nThis document is being created during the {current_phase} phase, with {progress:.1f}% of the project timeline completed.",
            "objectives": f"\n\nCurrent objectives reflect the team's progress through {current_phase} and readiness for upcoming phases.",
            "scope": f"\n\nThe project scope has been validated through {current_phase} activities and remains aligned with original planning.",
            "conclusion": f"\n\nNext steps will focus on completing {current_phase} and preparing for subsequent project phases."
        }

        return context_templates.get(section_name, "")

    def _generate_future_projections(self, timeline_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Generate future projections based on timeline intelligence."""
        future_events = []
        projections = {}

        # Extract future events
        for event in timeline_intelligence["timeline_events"]:
            if event.get("temporal_context") == "future":
                future_events.append(event)

        # Generate projections
        projections["upcoming_milestones"] = [
            event for event in future_events
            if event["type"] == TimelineEventType.MILESTONE.value
        ]

        projections["phase_transitions"] = [
            event for event in future_events
            if event["type"] == TimelineEventType.PHASE_START.value
        ]

        projections["timeline_projections"] = self._build_timeline_projections(timeline_intelligence)

        return projections

    def _build_timeline_projections(self, timeline_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Build detailed timeline projections."""
        metrics = timeline_intelligence["timeline_metrics"]
        remaining_days = metrics["remaining_duration_days"]

        return {
            "estimated_completion_date": datetime.now() + timedelta(days=remaining_days),
            "remaining_critical_path": timeline_intelligence["phase_progression"]["critical_path"],
            "risk_factors": self._identify_future_risks(timeline_intelligence),
            "recommended_actions": self._generate_future_recommendations(timeline_intelligence)
        }

    def _identify_future_risks(self, timeline_intelligence: Dict[str, Any]) -> List[str]:
        """Identify future risks based on timeline intelligence."""
        risks = []
        metrics = timeline_intelligence["timeline_metrics"]

        if metrics.get("time_pressure_factor", 1.0) > 1.5:
            risks.append("High time pressure may impact quality")

        if metrics.get("is_behind", False):
            risks.append("Schedule delays may affect remaining deliverables")

        upcoming_phases = timeline_intelligence["phase_progression"]["upcoming_phases"]
        if len(upcoming_phases) > 3:
            risks.append("Multiple upcoming phases may strain resources")

        return risks

    def _generate_future_recommendations(self, timeline_intelligence: Dict[str, Any]) -> List[str]:
        """Generate recommendations for future project phases."""
        recommendations = []
        metrics = timeline_intelligence["timeline_metrics"]

        if metrics.get("time_pressure_factor", 1.0) > 1.4:
            recommendations.append("Consider resource augmentation for remaining phases")

        if len(timeline_intelligence["phase_progression"]["upcoming_phases"]) > 2:
            recommendations.append("Plan detailed execution strategy for upcoming phases")

        recommendations.append("Maintain momentum from completed phases")
        recommendations.append("Leverage lessons learned for remaining work")

        return recommendations

    def _combine_temporal_content(self, historical: Dict[str, Any], current: Dict[str, Any],
                                future: Dict[str, Any], timeline_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Combine all temporal content aspects into final document."""
        combined = current.copy()

        # Add historical context
        combined["historical_context"] = historical

        # Add future projections
        combined["future_projections"] = future

        # Add timeline intelligence
        combined["timeline_intelligence"] = timeline_intelligence

        # Add temporal summary
        combined["temporal_summary"] = {
            "historical_insights": len(historical.get("lessons_learned", [])),
            "current_focus": timeline_intelligence["current_phase"]["name"],
            "future_commitments": len(future.get("upcoming_milestones", [])),
            "timeline_health": "good" if timeline_intelligence["timeline_metrics"]["progress_percentage"] > 60 else "needs_attention"
        }

        return combined


# Global timeline-aware generator instance
_timeline_aware_generator: Optional[TimelineAwareContentGenerator] = None


def get_timeline_aware_generator() -> TimelineAwareContentGenerator:
    """Get the global timeline-aware content generator instance."""
    global _timeline_aware_generator
    if _timeline_aware_generator is None:
        _timeline_aware_generator = TimelineAwareContentGenerator()
    return _timeline_aware_generator


__all__ = [
    'TimelineEventType',
    'TemporalRelationship',
    'TimelineAwareContentGenerator',
    'get_timeline_aware_generator'
]
