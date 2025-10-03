"""
Accuracy Enhancement Engine - Phase 9.6
Aggregates findings and enhances planning accuracy.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..entities.external_service_entities import (
    ExternalServiceMatch,
    ServiceCatalogEntry,
    ComplianceValidationResult,
    KnowledgeGapAnalysis,
    BlindspotAnalysis,
    AccuracyEnhancementResult,
    WorkflowEResult
)


class AccuracyEnhancementEngine:
    """
    Final engine that:
    - Aggregates all findings
    - Calculates story point corrections
    - Calculates timeline adjustments
    - Updates confidence scores
    - Generates feedback for Workflows A-D
    """
    
    def __init__(
        self,
        log_client=None
    ):
        """Initialize the accuracy enhancement engine."""
        self.log_client = log_client
    
    async def enhance_accuracy(
        self,
        original_plan: Dict[str, Any],
        discovered_services: List[ExternalServiceMatch],
        cataloged_services: List[ServiceCatalogEntry],
        validation_results: List[ComplianceValidationResult],
        gap_analyses: List[KnowledgeGapAnalysis],
        blindspot_analyses: List[BlindspotAnalysis],
        execution_time: float
    ) -> WorkflowEResult:
        """
        Enhance planning accuracy based on all findings.
        
        Args:
            original_plan: Original planning estimates
            discovered_services: Services discovered
            cataloged_services: Services cataloged
            validation_results: Validation findings
            gap_analyses: Gap detection findings
            blindspot_analyses: Blindspot detection findings
            execution_time: Time taken for Workflow E
        
        Returns:
            Complete Workflow E result with accuracy enhancement
        """
        if self.log_client:
            await self.log_client.log_info(
                "Starting accuracy enhancement aggregation"
            )
        
        # Extract original metrics
        original_sp = original_plan.get("story_points", 0)
        original_weeks = original_plan.get("weeks", 0.0)
        original_confidence = original_plan.get("confidence", 0)
        original_risk = original_plan.get("risk_level", "UNKNOWN")
        
        # Aggregate all story point additions
        validation_sp = sum(vr.total_story_points_to_add for vr in validation_results)
        gap_sp = sum(ga.total_story_points_to_add for ga in gap_analyses)
        blindspot_sp = sum(ba.total_story_points_missed for ba in blindspot_analyses)
        
        total_sp_added = validation_sp + gap_sp + blindspot_sp
        adjusted_sp = original_sp + total_sp_added
        sp_change_percent = (total_sp_added / original_sp * 100) if original_sp > 0 else 0
        
        # Aggregate all timeline impacts
        validation_days = sum(vr.total_timeline_impact_days for vr in validation_results)
        gap_days = sum(ga.total_timeline_impact_days for ga in gap_analyses)
        blindspot_days = sum(ba.total_timeline_impact_days for ba in blindspot_analyses)
        
        total_days_added = validation_days + gap_days + blindspot_days
        total_weeks_added = total_days_added / 5.0  # Convert to weeks
        adjusted_weeks = original_weeks + total_weeks_added
        timeline_change_percent = (total_weeks_added / original_weeks * 100) if original_weeks > 0 else 0
        
        # Calculate confidence improvement
        confidence_boost = self._calculate_confidence_boost(
            validation_results, gap_analyses, blindspot_analyses
        )
        adjusted_confidence = min(original_confidence + confidence_boost, 99)
        
        # Calculate risk reduction
        adjusted_risk, risk_reduction = self._calculate_risk_reduction(
            validation_results, gap_analyses, blindspot_analyses
        )
        
        # Count totals
        total_issues = sum(len(vr.issues) for vr in validation_results)
        total_gaps = sum(
            len(ga.documentation_gaps) + len(ga.skills_gaps) + len(ga.configuration_gaps)
            for ga in gap_analyses
        )
        total_blindspots = sum(len(ba.blindspots) for ba in blindspot_analyses)
        
        high_relevance_count = len([s for s in discovered_services if s.relevance_score >= 0.85])
        
        # Create comprehensive validation result (pick first one for now, or aggregate)
        primary_validation = validation_results[0] if validation_results else ComplianceValidationResult(
            service_id="none",
            api_compliant=True,
            security_compliant=True,
            version_compatible=True,
            rate_limits_sufficient=True,
            issues=[],
            total_story_points_to_add=0,
            total_timeline_impact_days=0.0,
            validation_confidence=1.0
        )
        
        # Create comprehensive gap analysis (pick first or aggregate)
        primary_gap = gap_analyses[0] if gap_analyses else KnowledgeGapAnalysis(
            service_id="none",
            documentation_gaps=[],
            skills_gaps=[],
            configuration_gaps=[],
            total_story_points_to_add=0,
            total_timeline_impact_days=0.0,
            enrichment_actions=[]
        )
        
        # Create comprehensive blindspot analysis (pick first or aggregate)
        primary_blindspot = blindspot_analyses[0] if blindspot_analyses else BlindspotAnalysis(
            service_id="none",
            blindspots=[],
            severity_distribution={},
            total_story_points_missed=0,
            total_timeline_impact_days=0.0,
            detection_confidence=1.0
        )
        
        # Create accuracy enhancement result
        accuracy_result = AccuracyEnhancementResult(
            original_story_points=original_sp,
            adjusted_story_points=adjusted_sp,
            story_points_added=total_sp_added,
            story_points_change_percent=sp_change_percent,
            original_weeks=original_weeks,
            adjusted_weeks=adjusted_weeks,
            weeks_added=total_weeks_added,
            timeline_change_percent=timeline_change_percent,
            original_confidence=original_confidence,
            adjusted_confidence=adjusted_confidence,
            confidence_improvement=confidence_boost,
            original_risk_level=original_risk,
            adjusted_risk_level=adjusted_risk,
            risk_reduction_percent=risk_reduction,
            validation_findings=primary_validation,
            gap_findings=primary_gap,
            blindspot_findings=primary_blindspot,
            services_discovered=len(discovered_services),
            high_relevance_services=high_relevance_count,
            issues_found_total=total_issues + total_gaps + total_blindspots,
            blindspots_detected=total_blindspots
        )
        
        # Create complete Workflow E result
        workflow_result = WorkflowEResult(
            discovered_services=discovered_services,
            cataloged_services=cataloged_services,
            validation_results=validation_results,
            gap_analyses=gap_analyses,
            blindspot_analyses=blindspot_analyses,
            accuracy_enhancement=accuracy_result,
            execution_time_seconds=execution_time
        )
        
        if self.log_client:
            await self.log_client.log_info(
                f"Accuracy enhancement complete: {original_confidence}% → {adjusted_confidence}% confidence",
                context={
                    "original_sp": original_sp,
                    "adjusted_sp": adjusted_sp,
                    "sp_added": total_sp_added,
                    "original_weeks": original_weeks,
                    "adjusted_weeks": adjusted_weeks,
                    "confidence_boost": confidence_boost,
                    "risk_reduction": risk_reduction
                }
            )
        
        return workflow_result
    
    def _calculate_confidence_boost(
        self,
        validation_results: List[ComplianceValidationResult],
        gap_analyses: List[KnowledgeGapAnalysis],
        blindspot_analyses: List[BlindspotAnalysis]
    ) -> int:
        """
        Calculate confidence boost from validation efforts.
        
        Factors:
        - Integration validated: +20 points
        - Blindspots detected: +18 points
        - Knowledge gaps identified: +15 points
        - Scale issues simulated: +12 points
        """
        boost = 0
        
        # Integration validation boost
        if validation_results:
            boost += 20
        
        # Blindspot detection boost
        if blindspot_analyses and any(ba.blindspots for ba in blindspot_analyses):
            boost += 18
        
        # Gap identification boost
        if gap_analyses:
            boost += 15
        
        return min(boost, 25)  # Cap at +25 points
    
    def _calculate_risk_reduction(
        self,
        validation_results: List[ComplianceValidationResult],
        gap_analyses: List[KnowledgeGapAnalysis],
        blindspot_analyses: List[BlindspotAnalysis]
    ) -> tuple[str, float]:
        """
        Calculate risk level and reduction percentage.
        
        Returns:
            (adjusted_risk_level, risk_reduction_percent)
        """
        # Calculate total critical/high issues found
        critical_high_count = 0
        
        for vr in validation_results:
            critical_high_count += len([
                i for i in vr.issues
                if i.severity.value in ["critical", "high"]
            ])
        
        for ba in blindspot_analyses:
            critical_high_count += ba.severity_distribution.get("critical", 0)
            critical_high_count += ba.severity_distribution.get("high", 0)
        
        # If we found and mitigated critical/high issues, risk is reduced
        if critical_high_count >= 5:
            return "LOW", 70.0  # Found and mitigated many issues
        elif critical_high_count >= 2:
            return "LOW", 60.0
        else:
            return "MEDIUM", 40.0
    
    async def generate_workflow_feedback(
        self,
        workflow_result: WorkflowEResult
    ) -> Dict[str, Any]:
        """
        Generate feedback for Workflows A-D based on findings.
        
        Returns dict with updates for each workflow.
        """
        feedback = {
            "workflow_a_updates": {
                "additional_stories": [],
                "additional_tasks": []
            },
            "workflow_c_updates": {
                "timeline_adjustments": {},
                "confidence_increase": 0
            },
            "workflow_d_updates": {
                "skills_training_added": [],
                "documentation_tasks_added": []
            }
        }
        
        # Extract validation issues as new stories/tasks
        for vr in workflow_result.validation_results:
            for issue in vr.issues:
                if issue.story_points_to_add > 0:
                    feedback["workflow_a_updates"]["additional_stories"].append({
                        "title": issue.issue,
                        "story_points": issue.story_points_to_add,
                        "sprint": issue.sprint
                    })
        
        # Extract blindspots as new stories/tasks
        for ba in workflow_result.blindspot_analyses:
            for blindspot in ba.blindspots:
                if blindspot.story_points_to_add > 0:
                    feedback["workflow_a_updates"]["additional_stories"].append({
                        "title": blindspot.description,
                        "story_points": blindspot.story_points_to_add,
                        "sprint": blindspot.sprint
                    })
        
        # Timeline adjustments for Workflow C
        acc = workflow_result.accuracy_enhancement
        feedback["workflow_c_updates"]["timeline_adjustments"] = {
            "validation_work_days": sum(vr.total_timeline_impact_days for vr in workflow_result.validation_results),
            "gap_filling_work_days": sum(ga.total_timeline_impact_days for ga in workflow_result.gap_analyses),
            "blindspot_mitigation_days": sum(ba.total_timeline_impact_days for ba in workflow_result.blindspot_analyses),
            "total_adjustment_days": acc.weeks_added * 5,
            "new_timeline_weeks": acc.adjusted_weeks
        }
        feedback["workflow_c_updates"]["confidence_increase"] = f"{acc.original_confidence}% → {acc.adjusted_confidence}%"
        
        # Skills and doc tasks for Workflow D
        for ga in workflow_result.gap_analyses:
            for gap in ga.skills_gaps:
                feedback["workflow_d_updates"]["skills_training_added"].append({
                    "description": gap.description,
                    "assignee": gap.assignee,
                    "effort_hours": sum(a.get("effort_hours", 0) for a in gap.remediation_actions)
                })
            
            for gap in ga.documentation_gaps:
                feedback["workflow_d_updates"]["documentation_tasks_added"].append({
                    "description": gap.description,
                    "assignee": gap.assignee,
                    "effort_hours": sum(a.get("effort_hours", 0) for a in gap.remediation_actions)
                })
        
        return feedback

