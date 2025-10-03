"""
Functional Test for Complete Workflow E
Tests the entire external service discovery, validation, and accuracy enhancement pipeline.
"""

import pytest
import asyncio
from datetime import datetime

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "services" / "project-planning-service"))

from domain.services.workflow_e_orchestrator import WorkflowEOrchestrator
from domain.entities.external_service_entities import WorkflowEResult


class MockLogClient:
    """Mock log client for testing."""
    async def log_info(self, message, context=None):
        print(f"INFO: {message}")
    
    async def log_warning(self, message, context=None):
        print(f"WARNING: {message}")
    
    async def log_error(self, message, context=None):
        print(f"ERROR: {message}")
    
    async def log_debug(self, message, context=None):
        pass


@pytest.mark.asyncio
async def test_complete_workflow_e():
    """Test the complete Workflow E pipeline."""
    print("\n" + "="*80)
    print("TESTING: Complete Workflow E - External Service Discovery & Accuracy Enhancement")
    print("="*80 + "\n")
    
    # Initialize orchestrator with mock clients
    orchestrator = WorkflowEOrchestrator(
        log_client=MockLogClient()
    )
    
    # Input data
    feature_query = """
    Build a real-time notification system that supports:
    - Push notifications for iOS and Android using Firebase
    - Email notifications using SendGrid
    - SMS notifications (future consideration)
    - Support for 100K users with peak loads
    - Real-time delivery tracking
    """
    
    extracted_requirements = {
        "feature_type": "Real-time Notification System",
        "integrations": ["Firebase FCM", "SendGrid", "APNs"],
        "expected_users": 100000,
        "platforms": ["iOS", "Android", "Web"]
    }
    
    original_plan = {
        "story_points": 68,
        "weeks": 4.0,
        "confidence": 78,
        "risk_level": "MEDIUM"
    }
    
    # Execute Workflow E
    print("🚀 Executing Workflow E...\n")
    result: WorkflowEResult = await orchestrator.execute_workflow_e(
        feature_query=feature_query,
        extracted_requirements=extracted_requirements,
        original_plan=original_plan
    )
    
    # Validate results
    print("\n" + "="*80)
    print("WORKFLOW E RESULTS")
    print("="*80 + "\n")
    
    # Phase 1: Discovery
    print(f"📍 Phase 1: Discovery")
    print(f"   Services Discovered: {len(result.discovered_services)}")
    print(f"   High Relevance (>0.85): {len([s for s in result.discovered_services if s.relevance_score >= 0.85])}")
    for service in result.discovered_services[:5]:
        print(f"   - {service.name}: {service.relevance_score:.2f} relevance")
    assert len(result.discovered_services) > 0, "Should discover services"
    
    # Phase 2: Cataloging
    print(f"\n📚 Phase 2: Cataloging")
    print(f"   Services Cataloged: {len(result.cataloged_services)}")
    for entry in result.cataloged_services[:3]:
        print(f"   - {entry.service_match.name}:")
        print(f"     Coverage: {entry.coverage_score:.2f}, Docs: {entry.documentation_quality}, Team: {len(entry.team_members)}")
    assert len(result.cataloged_services) > 0, "Should catalog services"
    
    # Phase 3: Validation
    print(f"\n✅ Phase 3: Validation")
    total_validation_issues = sum(len(vr.issues) for vr in result.validation_results)
    print(f"   Validation Results: {len(result.validation_results)}")
    print(f"   Total Issues Found: {total_validation_issues}")
    for vr in result.validation_results[:2]:
        if vr.issues:
            print(f"   - {vr.service_id}: {len(vr.issues)} issues, +{vr.total_story_points_to_add} SP")
            for issue in vr.issues[:2]:
                print(f"     • [{issue.severity.value.upper()}] {issue.issue}")
    
    # Phase 4: Gap Detection
    print(f"\n🕵️ Phase 4: Gap Detection")
    total_gaps = sum(
        len(ga.documentation_gaps) + len(ga.skills_gaps) + len(ga.configuration_gaps)
        for ga in result.gap_analyses
    )
    print(f"   Gap Analyses: {len(result.gap_analyses)}")
    print(f"   Total Gaps Found: {total_gaps}")
    for ga in result.gap_analyses[:2]:
        if ga.documentation_gaps or ga.skills_gaps or ga.configuration_gaps:
            print(f"   - {ga.service_id}:")
            print(f"     Doc: {len(ga.documentation_gaps)}, Skills: {len(ga.skills_gaps)}, Config: {len(ga.configuration_gaps)}")
    
    # Phase 5: Blindspot Detection
    print(f"\n🚨 Phase 5: Blindspot Detection")
    total_blindspots = sum(len(ba.blindspots) for ba in result.blindspot_analyses)
    print(f"   Blindspot Analyses: {len(result.blindspot_analyses)}")
    print(f"   Total Blindspots Found: {total_blindspots}")
    for ba in result.blindspot_analyses[:2]:
        if ba.blindspots:
            print(f"   - {ba.service_id}: {len(ba.blindspots)} blindspots, +{ba.total_story_points_missed} SP")
            for blindspot in ba.blindspots[:2]:
                print(f"     • [{blindspot.severity.value.upper()}] {blindspot.blindspot_type}: {blindspot.description[:60]}...")
    
    # Phase 6: Accuracy Enhancement
    print(f"\n📈 Phase 6: Accuracy Enhancement")
    acc = result.accuracy_enhancement
    print(f"   Original Plan:")
    print(f"     Story Points: {acc.original_story_points} SP")
    print(f"     Timeline: {acc.original_weeks} weeks")
    print(f"     Confidence: {acc.original_confidence}%")
    print(f"     Risk: {acc.original_risk_level}")
    print(f"\n   Enhanced Plan:")
    print(f"     Story Points: {acc.adjusted_story_points} SP (+{acc.story_points_added}, +{acc.story_points_change_percent:.1f}%)")
    print(f"     Timeline: {acc.adjusted_weeks:.1f} weeks (+{acc.weeks_added:.1f}, +{acc.timeline_change_percent:.1f}%)")
    print(f"     Confidence: {acc.adjusted_confidence}% (+{acc.confidence_improvement} points)")
    print(f"     Risk: {acc.adjusted_risk_level} (-{acc.risk_reduction_percent:.0f}%)")
    
    # Assertions
    assert acc.adjusted_story_points > acc.original_story_points, "Should add story points"
    assert acc.adjusted_confidence > acc.original_confidence, "Should improve confidence"
    assert acc.adjusted_weeks > acc.original_weeks, "Should adjust timeline"
    
    # Summary
    print(f"\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Services Discovered: {acc.services_discovered}")
    print(f"✅ High-Relevance Services: {acc.high_relevance_services}")
    print(f"✅ Total Issues Found: {acc.issues_found_total}")
    print(f"✅ Blindspots Detected: {acc.blindspots_detected}")
    print(f"✅ Accuracy Improvement: {acc.confidence_improvement} percentage points")
    print(f"✅ Story Points Corrected: +{acc.story_points_added} SP ({acc.story_points_change_percent:.1f}%)")
    print(f"✅ Timeline Adjusted: +{acc.weeks_added:.1f} weeks ({acc.timeline_change_percent:.1f}%)")
    print(f"✅ Execution Time: {result.execution_time_seconds:.2f}s")
    print(f"\n🎉 Workflow E executed successfully!\n")
    
    # Generate workflow feedback
    print("="*80)
    print("WORKFLOW FEEDBACK (for Workflows A-D)")
    print("="*80 + "\n")
    
    feedback = await orchestrator.get_workflow_feedback(result)
    
    print(f"📝 Workflow A Updates:")
    print(f"   Additional Stories: {len(feedback['workflow_a_updates']['additional_stories'])}")
    for story in feedback['workflow_a_updates']['additional_stories'][:3]:
        print(f"   - [{story['sprint']}] {story['title'][:60]}... (+{story['story_points']} SP)")
    
    print(f"\n⏱️  Workflow C Updates:")
    timeline_adj = feedback['workflow_c_updates']['timeline_adjustments']
    print(f"   Validation Work: +{timeline_adj.get('validation_work_days', 0):.1f} days")
    print(f"   Gap Filling: +{timeline_adj.get('gap_filling_work_days', 0):.1f} days")
    print(f"   Blindspot Mitigation: +{timeline_adj.get('blindspot_mitigation_days', 0):.1f} days")
    print(f"   Total Adjustment: +{timeline_adj.get('total_adjustment_days', 0):.1f} days")
    print(f"   New Timeline: {timeline_adj.get('new_timeline_weeks', 0):.1f} weeks")
    print(f"   Confidence: {feedback['workflow_c_updates']['confidence_increase']}")
    
    print(f"\n👥 Workflow D Updates:")
    print(f"   Skills Training: {len(feedback['workflow_d_updates']['skills_training_added'])}")
    print(f"   Documentation Tasks: {len(feedback['workflow_d_updates']['documentation_tasks_added'])}")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED - Workflow E is fully operational!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_complete_workflow_e())

