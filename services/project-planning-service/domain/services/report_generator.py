"""
Report Generator - Phase 5
Generates comprehensive 10-section professional reports from roadmap data.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum

from ..entities.feature import Feature, FeaturePriority
from ..entities.roadmap import Roadmap
from .roadmap_orchestrator import ComprehensiveRoadmap


class ReportFormat(Enum):
    """Supported report formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    PDF = "pdf"
    HTML = "html"


@dataclass
class ReportSection:
    """Individual report section."""
    number: int
    title: str
    content: str
    subsections: List['ReportSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComprehensiveReport:
    """Complete professional report."""
    report_id: str
    title: str
    generated_at: datetime
    roadmap_id: str
    memory_context_id: Optional[str] = None
    
    # All 10 sections
    sections: List[ReportSection] = field(default_factory=list)
    
    # Metadata
    total_pages: int = 0
    word_count: int = 0
    artifact_count: int = 0
    
    # Report settings
    format: ReportFormat = ReportFormat.MARKDOWN
    include_visualizations: bool = True
    include_artifacts: bool = True
    
    def get_section(self, number: int) -> Optional[ReportSection]:
        """Get section by number."""
        for section in self.sections:
            if section.number == number:
                return section
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_id": self.report_id,
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "roadmap_id": self.roadmap_id,
            "memory_context_id": self.memory_context_id,
            "sections": [
                {
                    "number": s.number,
                    "title": s.title,
                    "content": s.content,
                    "metadata": s.metadata
                }
                for s in self.sections
            ],
            "total_pages": self.total_pages,
            "word_count": self.word_count,
            "artifact_count": self.artifact_count,
            "format": self.format.value
        }


class ReportGenerator:
    """
    Professional report generator for comprehensive roadmaps.
    
    Generates 10-section reports suitable for:
    - Executive presentations
    - Team planning
    - Stakeholder communications
    - PM tool imports
    """
    
    def __init__(self):
        """Initialize report generator."""
        self.section_generators = {
            1: self._generate_executive_summary,
            2: self._generate_scope_objectives,
            3: self._generate_timeline_milestones,
            4: self._generate_resource_allocation,
            5: self._generate_feature_decomposition,
            6: self._generate_risk_assessment,
            7: self._generate_dependencies_blockers,
            8: self._generate_historical_context,
            9: self._generate_recommendations,
            10: self._generate_appendices
        }
    
    async def generate_comprehensive_report(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]] = None,
        format: ReportFormat = ReportFormat.MARKDOWN,
        sections: Optional[List[int]] = None
    ) -> ComprehensiveReport:
        """
        Generate complete professional report.
        
        Args:
            roadmap: Comprehensive roadmap data
            memory_context: Memory agent context (optional)
            format: Output format
            sections: Specific sections to generate (None = all)
            
        Returns:
            ComprehensiveReport with all requested sections
        """
        import uuid
        
        report_id = f"report-{uuid.uuid4().hex[:8]}"
        
        report = ComprehensiveReport(
            report_id=report_id,
            title=f"Development Roadmap Report - {roadmap.roadmap.name}",
            generated_at=datetime.utcnow(),
            roadmap_id=roadmap.roadmap.id,
            memory_context_id=memory_context.get("context_id") if memory_context else None,
            format=format
        )
        
        # Generate requested sections
        section_numbers = sections if sections else list(range(1, 11))
        
        for num in section_numbers:
            if num in self.section_generators:
                section = await self.section_generators[num](roadmap, memory_context)
                report.sections.append(section)
        
        # Calculate metadata
        report = self._calculate_report_metadata(report)
        
        return report
    
    async def _generate_executive_summary(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]]
    ) -> ReportSection:
        """Section 1: Executive Summary."""
        summary = roadmap.summary()
        
        content = f"""# Executive Summary

## Project Overview
**Project:** {roadmap.roadmap.name}
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
**Roadmap ID:** {roadmap.roadmap.id}

## Key Metrics
- **Total Features:** {summary['total_features']}
- **Total Story Points:** {summary['total_story_points']:.1f}
- **Estimated Timeline:** {summary['timeline_duration_weeks']} weeks
- **Estimated Completion:** {summary['estimated_completion']}
- **Team Velocity:** {roadmap.generation_result.roadmap.metadata.get('team_velocity', 'N/A')} SP/sprint
- **Confidence Score:** {summary['confidence_score']:.0%}

## Resource Requirements
- **Team Size:** {len(roadmap.decomposition_results) if roadmap.decomposition_results else 'TBD'}
- **Sprint Count:** {len(roadmap.generation_result.sprints)}
- **Milestone Count:** {len(roadmap.milestone_plan.milestones) if roadmap.milestone_plan else 0}

## Risk Summary
- **High Priority Risks:** {len([r for r in roadmap.generation_result.warnings if 'risk' in r.lower()])}
- **Blockers Identified:** {len([w for w in roadmap.generation_result.warnings if 'block' in w.lower()])}
- **Mitigation Required:** {'Yes' if roadmap.generation_result.warnings else 'No'}

## Status
**Overall Status:** {'🟢 On Track' if summary['confidence_score'] > 0.7 else '🟡 Needs Attention'}
**Ready for Execution:** {'Yes ✅' if summary['total_features'] > 0 else 'Pending ⏳'}
"""
        
        return ReportSection(
            number=1,
            title="Executive Summary",
            content=content,
            metadata={
                "metrics": {
                    "features": summary['total_features'],
                    "story_points": summary['total_story_points'],
                    "timeline_weeks": summary['timeline_duration_weeks'],
                    "confidence": summary['confidence_score']
                }
            }
        )
    
    async def _generate_scope_objectives(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]]
    ) -> ReportSection:
        """Section 2: Project Scope & Objectives."""
        features = roadmap.roadmap.features if hasattr(roadmap.roadmap, 'features') else []
        
        content = f"""# Project Scope & Objectives

## Features Overview
Total features planned: **{len(features)}**

"""
        
        # Group features by priority
        high_priority = [f for f in features if f.priority == FeaturePriority.HIGH]
        medium_priority = [f for f in features if f.priority == FeaturePriority.MEDIUM]
        low_priority = [f for f in features if f.priority == FeaturePriority.LOW]
        
        if high_priority:
            content += f"\n### High Priority Features ({len(high_priority)})\n\n"
            for f in high_priority[:10]:  # Limit to first 10
                content += f"- **{f.title}** - {f.estimated_effort:.1f} SP\n"
                if f.description:
                    content += f"  - {f.description[:100]}{'...' if len(f.description) > 100 else ''}\n"
        
        if medium_priority:
            content += f"\n### Medium Priority Features ({len(medium_priority)})\n\n"
            for f in medium_priority[:10]:
                content += f"- **{f.title}** - {f.estimated_effort:.1f} SP\n"
        
        if low_priority:
            content += f"\n### Low Priority Features ({len(low_priority)})\n\n"
            for f in low_priority[:5]:
                content += f"- **{f.title}** - {f.estimated_effort:.1f} SP\n"
        
        content += f"""

## Business Goals
- Deliver high-value features first
- Maintain consistent velocity
- Minimize technical debt
- Ensure quality standards

## Success Criteria
- All high-priority features completed
- Velocity within 10% of estimate
- < 5% post-release defects
- Team satisfaction > 80%

## Constraints
- Timeline: {roadmap.generation_result.roadmap.created_at.strftime('%Y-%m-%d')} onwards
- Team capacity: Based on velocity
- Technical stack: As specified per feature
- Budget: To be determined
"""
        
        return ReportSection(
            number=2,
            title="Project Scope & Objectives",
            content=content,
            metadata={
                "feature_count": len(features),
                "priority_breakdown": {
                    "high": len(high_priority),
                    "medium": len(medium_priority),
                    "low": len(low_priority)
                }
            }
        )
    
    async def _generate_timeline_milestones(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]]
    ) -> ReportSection:
        """Section 3: Timeline & Milestones."""
        content = f"""# Timeline & Milestones

## Project Timeline
**Start Date:** {roadmap.roadmap.start_date.strftime('%Y-%m-%d')}
**Estimated End:** {roadmap.timeline_estimate.estimated_completion_date.strftime('%Y-%m-%d') if roadmap.timeline_estimate else 'TBD'}
**Duration:** {roadmap.timeline_estimate.total_weeks if roadmap.timeline_estimate else 0} weeks

## Sprint Breakdown
"""
        
        if roadmap.generation_result.sprints:
            content += f"Total Sprints: **{len(roadmap.generation_result.sprints)}**\n\n"
            for i, sprint in enumerate(roadmap.generation_result.sprints[:10], 1):
                content += f"### Sprint {i}\n"
                content += f"- **Dates:** {sprint.start_date.strftime('%Y-%m-%d')} to {sprint.end_date.strftime('%Y-%m-%d')}\n"
                content += f"- **Capacity:** {sprint.capacity:.1f} SP\n"
                content += f"- **Features:** {len(sprint.feature_ids)}\n"
                content += f"- **Status:** {sprint.status.value if hasattr(sprint, 'status') else 'Planned'}\n\n"
        
        if roadmap.milestone_plan:
            content += f"\n## Key Milestones\n"
            content += f"Total Milestones: **{len(roadmap.milestone_plan.milestones)}**\n\n"
            for milestone in roadmap.milestone_plan.milestones:
                content += f"### {milestone.name}\n"
                content += f"- **Target Date:** {milestone.target_date.strftime('%Y-%m-%d')}\n"
                content += f"- **Type:** {milestone.milestone_type.value}\n"
                content += f"- **Features:** {len(milestone.feature_ids)}\n"
                content += f"- **Story Points:** {milestone.story_points:.1f}\n"
                content += f"- **Status:** {'✅ Completed' if milestone.completed else '⏳ Pending'}\n\n"
        
        content += f"""
## Critical Path
{roadmap.dependency_analysis.critical_path_length if roadmap.dependency_analysis else 'N/A'} story points

## Timeline Confidence
- **Best Case:** {roadmap.timeline_estimate.best_case_weeks if roadmap.timeline_estimate else 'N/A'} weeks
- **Most Likely:** {roadmap.timeline_estimate.most_likely_weeks if roadmap.timeline_estimate else 'N/A'} weeks
- **Worst Case:** {roadmap.timeline_estimate.worst_case_weeks if roadmap.timeline_estimate else 'N/A'} weeks
- **Confidence:** {roadmap.timeline_estimate.confidence if roadmap.timeline_estimate else 'N/A'}
"""
        
        return ReportSection(
            number=3,
            title="Timeline & Milestones",
            content=content,
            metadata={
                "sprint_count": len(roadmap.generation_result.sprints),
                "milestone_count": len(roadmap.milestone_plan.milestones) if roadmap.milestone_plan else 0,
                "duration_weeks": roadmap.timeline_estimate.total_weeks if roadmap.timeline_estimate else 0
            }
        )
    
    async def _generate_resource_allocation(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]]
    ) -> ReportSection:
        """Section 4: Resource Allocation."""
        content = """# Resource Allocation

## Team Composition
"""
        
        if memory_context and "team_members" in memory_context:
            team = memory_context["team_members"]
            content += f"Team Size: **{len(team)}** members\n\n"
            for member in team:
                content += f"### {member.get('name', 'Team Member')}\n"
                content += f"- **Role:** {member.get('role', 'Developer')}\n"
                content += f"- **Skills:** {', '.join(member.get('skills', []))}\n"
                content += f"- **Capacity:** {member.get('capacity', 40)} hours/sprint\n\n"
        else:
            content += "Team details to be provided by User Store integration.\n\n"
        
        content += f"""
## Capacity Planning
- **Velocity:** {roadmap.generation_result.roadmap.metadata.get('team_velocity', 'TBD')} SP/sprint
- **Sprint Duration:** {roadmap.generation_result.roadmap.metadata.get('sprint_duration', 2)} weeks
- **Total Capacity:** {roadmap.timeline_estimate.total_capacity if roadmap.timeline_estimate else 'TBD'} SP

## Assignment Strategy
- Skills-based matching
- Load balancing across team
- Dependency consideration
- Risk mitigation through pairing

## Utilization
- **Target:** 85% capacity utilization
- **Buffer:** 15% for unexpected work
- **Meeting Time:** Included in capacity planning
"""
        
        return ReportSection(
            number=4,
            title="Resource Allocation",
            content=content,
            metadata={
                "velocity": roadmap.generation_result.roadmap.metadata.get('team_velocity', 0)
            }
        )
    
    async def _generate_feature_decomposition(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]]
    ) -> ReportSection:
        """Section 5: Feature Decomposition."""
        content = """# Feature Decomposition

## Decomposition Summary
"""
        
        if roadmap.decomposition_results:
            content += f"Features Decomposed: **{len(roadmap.decomposition_results)}**\n\n"
            
            total_stories = sum(d.user_story_count for d in roadmap.decomposition_results.values())
            total_tasks = sum(d.technical_task_count for d in roadmap.decomposition_results.values())
            
            content += f"- **Total User Stories:** {total_stories}\n"
            content += f"- **Total Technical Tasks:** {total_tasks}\n"
            content += f"- **Average Story Points/Feature:** {sum(d.estimated_effort for d in roadmap.decomposition_results.values()) / len(roadmap.decomposition_results):.1f}\n\n"
            
            # Show first few decompositions
            for feature_id, decomp in list(roadmap.decomposition_results.items())[:5]:
                content += f"### Feature: {feature_id}\n"
                content += f"- **User Stories:** {decomp.user_story_count}\n"
                content += f"- **Technical Tasks:** {decomp.technical_task_count}\n"
                content += f"- **Story Points:** {decomp.estimated_effort:.1f}\n"
                content += f"- **Complexity:** {decomp.complexity_factors.get('overall', 'Medium')}\n\n"
        else:
            content += "Feature decomposition pending or not requested.\n\n"
        
        content += """
## Estimation Methodology
- Fibonacci scale (1, 2, 3, 5, 8, 13, 21)
- Team-based planning poker
- Historical velocity reference
- Complexity factor adjustment

## Acceptance Criteria
Defined for each user story with:
- Clear definition of done
- Testable conditions
- Performance requirements
- Security considerations
"""
        
        return ReportSection(
            number=5,
            title="Feature Decomposition",
            content=content,
            metadata={
                "features_decomposed": len(roadmap.decomposition_results) if roadmap.decomposition_results else 0
            }
        )
    
    async def _generate_risk_assessment(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]]
    ) -> ReportSection:
        """Section 6: Risk Assessment."""
        warnings = roadmap.generation_result.warnings
        
        content = f"""# Risk Assessment

## Risk Summary
Total Risks Identified: **{len(warnings)}**

"""
        
        if warnings:
            # Categorize risks
            technical_risks = [w for w in warnings if any(t in w.lower() for t in ['technical', 'complexity', 'dependency'])]
            schedule_risks = [w for w in warnings if any(t in w.lower() for t in ['schedule', 'timeline', 'capacity'])]
            resource_risks = [w for w in warnings if any(t in w.lower() for t in ['resource', 'team', 'skill'])]
            other_risks = [w for w in warnings if w not in technical_risks + schedule_risks + resource_risks]
            
            if technical_risks:
                content += f"### Technical Risks ({len(technical_risks)})\n\n"
                for risk in technical_risks:
                    content += f"- ⚠️ {risk}\n"
                content += "\n"
            
            if schedule_risks:
                content += f"### Schedule Risks ({len(schedule_risks)})\n\n"
                for risk in schedule_risks:
                    content += f"- ⏰ {risk}\n"
                content += "\n"
            
            if resource_risks:
                content += f"### Resource Risks ({len(resource_risks)})\n\n"
                for risk in resource_risks:
                    content += f"- 👥 {risk}\n"
                content += "\n"
            
            if other_risks:
                content += f"### Other Risks ({len(other_risks)})\n\n"
                for risk in other_risks:
                    content += f"- 🔔 {risk}\n"
                content += "\n"
        else:
            content += "No significant risks identified at this time.\n\n"
        
        content += """
## Risk Mitigation Strategies
1. **Technical Debt Management:** Regular refactoring sprints
2. **Schedule Buffers:** 15% contingency built into estimates
3. **Resource Planning:** Cross-training and knowledge sharing
4. **Regular Reviews:** Weekly risk assessment and adjustment

## Contingency Plans
- Additional resources available if needed
- Scope adjustment process defined
- Technical spike allocation: 10% per sprint
- Escalation path established
"""
        
        return ReportSection(
            number=6,
            title="Risk Assessment",
            content=content,
            metadata={
                "total_risks": len(warnings),
                "risk_categories": {
                    "technical": len([w for w in warnings if 'technical' in w.lower()]),
                    "schedule": len([w for w in warnings if 'schedule' in w.lower()]),
                    "resource": len([w for w in warnings if 'resource' in w.lower()])
                }
            }
        )
    
    async def _generate_dependencies_blockers(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]]
    ) -> ReportSection:
        """Section 7: Dependencies & Blockers."""
        content = """# Dependencies & Blockers

"""
        
        if roadmap.dependency_analysis:
            dep_analysis = roadmap.dependency_analysis
            content += f"""## Dependency Analysis
- **Total Dependencies:** {dep_analysis.total_dependencies}
- **Critical Path Length:** {dep_analysis.critical_path_length} SP
- **Bottlenecks Identified:** {dep_analysis.bottleneck_count}
- **Max Parallelism:** {dep_analysis.max_parallel_features}

## Dependency Graph
"""
            if dep_analysis.execution_order:
                content += "Recommended execution order based on dependencies:\n\n"
                for i, feature_id in enumerate(dep_analysis.execution_order[:10], 1):
                    content += f"{i}. {feature_id}\n"
        else:
            content += "Dependency analysis not performed or not available.\n"
        
        content += """

## Blocker Management
- **Identification:** Daily standup and sprint planning
- **Resolution:** Dedicated blocker resolution time
- **Escalation:** Clear escalation path defined
- **Tracking:** Blocker board maintained

## External Dependencies
- Third-party API availability
- Infrastructure provisioning
- Security approvals
- Design asset delivery

## Mitigation Strategies
1. Early identification of dependencies
2. Parallel work streams where possible
3. Regular dependency review meetings
4. Clear communication channels
"""
        
        return ReportSection(
            number=7,
            title="Dependencies & Blockers",
            content=content,
            metadata={
                "total_dependencies": roadmap.dependency_analysis.total_dependencies if roadmap.dependency_analysis else 0,
                "critical_path": roadmap.dependency_analysis.critical_path_length if roadmap.dependency_analysis else 0
            }
        )
    
    async def _generate_historical_context(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]]
    ) -> ReportSection:
        """Section 8: Historical Context."""
        content = """# Historical Context

"""
        
        if memory_context and "historical_data" in memory_context:
            hist_data = memory_context["historical_data"]
            content += f"""## Similar Past Features
Found **{hist_data.get('similar_features', 0)}** similar features in history.

### Key Findings
- Average completion time: {hist_data.get('avg_completion_weeks', 'N/A')} weeks
- Average story points: {hist_data.get('avg_story_points', 'N/A')} SP
- Success rate: {hist_data.get('success_rate', 'N/A')}%

### Lessons Learned
"""
            for lesson in hist_data.get('lessons', []):
                content += f"- {lesson}\n"
        else:
            content += "Historical context data not available. This would typically include:\n"
            content += "- Similar past features\n"
            content += "- Team velocity trends\n"
            content += "- Lessons learned\n"
            content += "- Best practices\n"
        
        content += """

## Velocity Trends
Historical team velocity analysis helps calibrate estimates and identify capacity patterns.

## Best Practices
Based on past experiences:
1. Early technical spikes reduce surprises
2. Incremental delivery reduces risk
3. Regular stakeholder demos improve alignment
4. Code reviews maintain quality

## Known Pitfalls
Areas to watch based on historical data:
- Underestimated integration complexity
- Scope creep in user stories
- Technical debt accumulation
- Communication gaps
"""
        
        return ReportSection(
            number=8,
            title="Historical Context",
            content=content,
            metadata={
                "similar_features_found": memory_context.get("historical_data", {}).get("similar_features", 0) if memory_context else 0
            }
        )
    
    async def _generate_recommendations(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]]
    ) -> ReportSection:
        """Section 9: Recommendations."""
        recommendations = roadmap.recommendations
        
        content = f"""# Recommendations

Total Recommendations: **{len(recommendations)}**

"""
        
        if recommendations:
            # Categorize recommendations
            priority_recs = [r for r in recommendations if any(t in r.lower() for t in ['high', 'critical', 'urgent'])]
            process_recs = [r for r in recommendations if any(t in r.lower() for t in ['process', 'workflow', 'practice'])]
            technical_recs = [r for r in recommendations if any(t in r.lower() for t in ['technical', 'architecture', 'code'])]
            team_recs = [r for r in recommendations if any(t in r.lower() for t in ['team', 'resource', 'skill'])]
            
            if priority_recs:
                content += "## High Priority\n\n"
                for rec in priority_recs:
                    content += f"- 🔴 {rec}\n"
                content += "\n"
            
            if process_recs:
                content += "## Process Improvements\n\n"
                for rec in process_recs:
                    content += f"- 🔄 {rec}\n"
                content += "\n"
            
            if technical_recs:
                content += "## Technical Recommendations\n\n"
                for rec in technical_recs:
                    content += f"- 🔧 {rec}\n"
                content += "\n"
            
            if team_recs:
                content += "## Team & Resource\n\n"
                for rec in team_recs:
                    content += f"- 👥 {rec}\n"
                content += "\n"
        
        content += """
## Success Factors
1. **Executive Sponsorship:** Ensure leadership support
2. **Clear Communication:** Regular stakeholder updates
3. **Quality Focus:** Maintain code and process standards
4. **Team Morale:** Keep team engaged and motivated
5. **Flexibility:** Adapt to changing requirements

## Next Steps
1. Review and approve roadmap
2. Confirm team assignments
3. Set up infrastructure
4. Schedule kickoff meeting
5. Begin Sprint 1
"""
        
        return ReportSection(
            number=9,
            title="Recommendations",
            content=content,
            metadata={
                "total_recommendations": len(recommendations)
            }
        )
    
    async def _generate_appendices(
        self,
        roadmap: ComprehensiveRoadmap,
        memory_context: Optional[Dict[str, Any]]
    ) -> ReportSection:
        """Section 10: Appendices."""
        content = """# Appendices

## A. Detailed Feature List
"""
        
        features = roadmap.roadmap.features if hasattr(roadmap.roadmap, 'features') else []
        for feature in features[:20]:  # Limit to first 20
            content += f"\n### {feature.title}\n"
            content += f"- **ID:** {feature.id}\n"
            content += f"- **Priority:** {feature.priority.value}\n"
            content += f"- **Effort:** {feature.estimated_effort:.1f} SP\n"
            if feature.description:
                content += f"- **Description:** {feature.description}\n"
            if feature.dependencies:
                content += f"- **Dependencies:** {', '.join(feature.dependencies)}\n"
        
        content += "\n## B. Artifact References\n"
        if memory_context and "artifacts" in memory_context:
            artifacts = memory_context["artifacts"]
            content += f"Total artifacts linked: **{len(artifacts)}**\n\n"
            for artifact in artifacts[:10]:
                content += f"- {artifact.get('type', 'Unknown')}: {artifact.get('id', 'N/A')}\n"
        else:
            content += "Artifact references available in Memory Agent.\n"
        
        content += """

## C. API Links
- Project Planning API: http://localhost:8000/api/v1/
- Memory Agent API: http://localhost:5090/api/v1/
- Doc Store API: http://localhost:5140/api/v1/
- User Store API: http://localhost:8002/api/v1/

## D. Glossary
- **SP:** Story Points
- **DDD:** Domain-Driven Design
- **PR:** Pull Request
- **MVP:** Minimum Viable Product
- **DoD:** Definition of Done

## E. Contact Information
- **Project Manager:** TBD
- **Tech Lead:** TBD
- **Product Owner:** TBD
- **Scrum Master:** TBD

## F. Change Log
This report is dynamically generated. For change history, refer to the Memory Agent context.
"""
        
        return ReportSection(
            number=10,
            title="Appendices",
            content=content,
            metadata={
                "feature_count": len(features)
            }
        )
    
    def _calculate_report_metadata(self, report: ComprehensiveReport) -> ComprehensiveReport:
        """Calculate report metadata (word count, page count, etc.)."""
        total_words = 0
        for section in report.sections:
            total_words += len(section.content.split())
        
        report.word_count = total_words
        report.total_pages = max(1, total_words // 500)  # Rough estimate: 500 words/page
        report.artifact_count = sum(
            s.metadata.get('artifact_count', 0)
            for s in report.sections
        )
        
        return report

