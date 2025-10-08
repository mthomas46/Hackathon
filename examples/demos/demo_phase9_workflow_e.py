"""
Phase 9 Demo: Workflow E - External Service Discovery, Validation & Accuracy Enhancement
Demonstrates the complete pipeline and generates a beautiful markdown report.
"""

import asyncio
import sys
from pathlib import Path

# Add services directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "services" / "project-planning-service"))

from domain.services.workflow_e_orchestrator import WorkflowEOrchestrator
from domain.services.beautiful_markdown_formatter import BeautifulMarkdownFormatter


class MockLogClient:
    """Mock log client for demo."""
    async def log_info(self, message, context=None):
        print(f"ℹ️  {message}")
    
    async def log_warning(self, message, context=None):
        print(f"⚠️  {message}")
    
    async def log_error(self, message, context=None):
        print(f"❌ {message}")
    
    async def log_debug(self, message, context=None):
        pass


async def main():
    """Run the Phase 9 demo."""
    print("\n" + "="*100)
    print(" "*30 + "🚀 PHASE 9 DEMONSTRATION 🚀")
    print(" "*15 + "Workflow E: External Service Discovery, Validation & Accuracy Enhancement")
    print("="*100 + "\n")
    
    # Initialize orchestrator
    print("🔧 Initializing Workflow E Orchestrator...")
    orchestrator = WorkflowEOrchestrator(
        log_client=MockLogClient()
    )
    
    # Define feature request
    feature_name = "Real-time Notification System"
    feature_query = """
    Build a comprehensive real-time notification system that supports:
    - Push notifications for iOS and Android using Firebase Cloud Messaging
    - Email notifications using SendGrid for transactional and marketing emails
    - SMS notifications (future consideration via Twilio)
    - Support for 100,000 users with peak loads of 50,000 notifications per hour
    - Real-time delivery tracking and analytics
    - User notification preferences and opt-out management
    - Multi-language support for notification templates
    """
    
    extracted_requirements = {
        "feature_type": "Real-time Notification System",
        "integrations": ["Firebase FCM", "SendGrid", "Apple APNs"],
        "expected_users": 100000,
        "peak_load": 50000,
        "platforms": ["iOS", "Android", "Web"],
        "priority": "High",
        "complexity": "High"
    }
    
    original_plan = {
        "story_points": 68,
        "weeks": 4.0,
        "confidence": 78,
        "risk_level": "MEDIUM"
    }
    
    print(f"\n📋 Feature: {feature_name}")
    print(f"   Expected Users: {extracted_requirements['expected_users']:,}")
    print(f"   Peak Load: {extracted_requirements['peak_load']:,} notifications/hour")
    print(f"   Platforms: {', '.join(extracted_requirements['platforms'])}")
    
    print(f"\n📊 Original Plan Estimates:")
    print(f"   Story Points: {original_plan['story_points']} SP")
    print(f"   Timeline: {original_plan['weeks']} weeks")
    print(f"   Confidence: {original_plan['confidence']}%")
    print(f"   Risk Level: {original_plan['risk_level']}")
    
    print("\n" + "="*100)
    print("EXECUTING WORKFLOW E")
    print("="*100 + "\n")
    
    # Execute Workflow E
    result = await orchestrator.execute_workflow_e(
        feature_query=feature_query,
        extracted_requirements=extracted_requirements,
        original_plan=original_plan
    )
    
    print("\n" + "="*100)
    print("WORKFLOW E RESULTS")
    print("="*100 + "\n")
    
    acc = result.accuracy_enhancement
    
    print(f"✅ PHASE 1 - Discovery:")
    print(f"   • {len(result.discovered_services)} external services discovered")
    print(f"   • {len([s for s in result.discovered_services if s.relevance_score >= 0.85])} high-relevance services")
    
    print(f"\n✅ PHASE 2 - Cataloging:")
    print(f"   • {len(result.cataloged_services)} services cataloged with full relationships")
    print(f"   • Average coverage score: {sum(s.coverage_score for s in result.cataloged_services) / len(result.cataloged_services):.0%}")
    
    print(f"\n✅ PHASE 3 - Validation:")
    total_validation_issues = sum(len(vr.issues) for vr in result.validation_results)
    print(f"   • {len(result.validation_results)} services validated")
    print(f"   • {total_validation_issues} compliance issues found")
    print(f"   • +{sum(vr.total_story_points_to_add for vr in result.validation_results)} SP to add")
    
    print(f"\n✅ PHASE 4 - Gap Detection:")
    total_gaps = sum(
        len(ga.documentation_gaps) + len(ga.skills_gaps) + len(ga.configuration_gaps)
        for ga in result.gap_analyses
    )
    print(f"   • {total_gaps} knowledge gaps identified")
    print(f"   • +{sum(ga.total_story_points_to_add for ga in result.gap_analyses)} SP to add")
    
    print(f"\n✅ PHASE 5 - Blindspot Detection:")
    total_blindspots = sum(len(ba.blindspots) for ba in result.blindspot_analyses)
    critical_blindspots = sum(ba.severity_distribution.get("critical", 0) for ba in result.blindspot_analyses)
    print(f"   • {total_blindspots} development blindspots detected")
    print(f"   • {critical_blindspots} critical blindspots")
    print(f"   • +{sum(ba.total_story_points_missed for ba in result.blindspot_analyses)} SP to add")
    
    print(f"\n✅ PHASE 6 - Accuracy Enhancement:")
    print(f"   • Confidence: {acc.original_confidence}% → {acc.adjusted_confidence}% (+{acc.confidence_improvement} points)")
    print(f"   • Story Points: {acc.original_story_points} → {acc.adjusted_story_points} (+{acc.story_points_added} SP, +{acc.story_points_change_percent:.1f}%)")
    print(f"   • Timeline: {acc.original_weeks:.1f} → {acc.adjusted_weeks:.1f} weeks (+{acc.weeks_added:.1f} weeks, +{acc.timeline_change_percent:.1f}%)")
    print(f"   • Risk: {acc.original_risk_level} → {acc.adjusted_risk_level} (-{acc.risk_reduction_percent:.0f}%)")
    
    print("\n" + "="*100)
    print("GENERATING BEAUTIFUL MARKDOWN REPORT")
    print("="*100 + "\n")
    
    # Generate beautiful markdown report
    formatter = BeautifulMarkdownFormatter()
    markdown_report = formatter.generate_complete_report(result, feature_name)
    
    # Save to file
    report_filename = project_root / f"PHASE9_WORKFLOW_E_REPORT_{feature_name.replace(' ', '_')}.md"
    formatter.save_to_file(markdown_report, str(report_filename))
    
    print(f"✅ Report generated: {report_filename.name}")
    print(f"   • Length: {len(markdown_report):,} characters")
    print(f"   • Sections: 5 (Sections 11-15)")
    print(f"   • Services Analyzed: {len(result.discovered_services)}")
    print(f"   • Issues Documented: {acc.issues_found_total}")
    
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100 + "\n")
    
    print(f"🎯 **Key Achievements:**")
    print(f"   ✅ Discovered and cataloged {acc.services_discovered} external services")
    print(f"   ✅ Validated {len(result.validation_results)} services for compliance")
    print(f"   ✅ Detected {acc.issues_found_total} issues that would have blocked delivery")
    print(f"   ✅ Found {acc.blindspots_detected} hidden blindspots")
    print(f"   ✅ Increased confidence by {acc.confidence_improvement} percentage points")
    print(f"   ✅ Corrected estimate by +{acc.story_points_added} SP (+{acc.story_points_change_percent:.0f}%)")
    print(f"   ✅ Adjusted timeline by +{acc.weeks_added:.1f} weeks for accuracy")
    print(f"   ✅ Reduced risk by {acc.risk_reduction_percent:.0f}%")
    
    print(f"\n💡 **Bottom Line:**")
    print(f"   Without Workflow E, this project would have:")
    print(f"   • Underestimated by {acc.story_points_added} story points ({acc.story_points_change_percent:.0f}%)")
    print(f"   • Discovered {acc.issues_found_total} issues during development (costly)")
    print(f"   • Likely overrun timeline by {acc.weeks_added:.1f}+ weeks")
    print(f"   • Faced {critical_blindspots} critical integration failures")
    print(f"   • Had {acc.original_confidence}% confidence instead of {acc.adjusted_confidence}%")
    
    print(f"\n⚡ **Workflow E Performance:**")
    print(f"   • Execution Time: {result.execution_time_seconds:.2f} seconds")
    print(f"   • Services Analyzed: {acc.services_discovered}")
    print(f"   • Issues Found: {acc.issues_found_total}")
    print(f"   • Accuracy Improvement: +{acc.confidence_improvement} points")
    
    print("\n" + "="*100)
    print(f"✅ Phase 9 Demo Complete! Report saved to: {report_filename.name}")
    print("="*100 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

