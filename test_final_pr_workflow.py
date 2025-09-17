#!/usr/bin/env python3
"""
Final PR Confidence Analysis Workflow Test

Demonstrates the complete workflow with all analysis modules.
"""

import asyncio
import json
import time
from datetime import datetime

# Import analysis modules
from services.orchestrator.modules.analysis.pr_cross_reference_analyzer import pr_cross_reference_analyzer
from services.orchestrator.modules.analysis.pr_confidence_scorer import pr_confidence_scorer
from services.orchestrator.modules.analysis.pr_gap_detector import pr_gap_detector

async def test_complete_workflow():
    """Test the complete PR confidence analysis workflow."""
    print("🚀 FINAL PR CONFIDENCE ANALYSIS WORKFLOW TEST")
    print("=" * 60)

    # Mock data
    pr_data = {
        "id": "PR-12345",
        "title": "Implement OAuth2 Authentication Service",
        "description": "OAuth2 implementation with token validation",
        "author": "developer@example.com",
        "files_changed": ["src/auth/oauth2_client.py", "src/auth/middleware.py"],
        "jira_ticket": "PROJ-456"
    }

    jira_data = {
        "id": "PROJ-456",
        "title": "Implement OAuth2 Authentication",
        "acceptance_criteria": ["OAuth2 flow", "Token validation", "Documentation"],
        "priority": "High"
    }

    confluence_docs = [{
        "id": "API_DOCS",
        "title": "API Documentation",
        "content": "Authentication endpoints and security requirements"
    }]

    print("📊 Running Cross-Reference Analysis...")
    cross_ref = pr_cross_reference_analyzer.perform_comprehensive_cross_reference(
        pr_data, jira_data, confluence_docs
    )
    print(f"   Alignment: {cross_ref.overall_alignment_score:.1%}")
    print(f"   Gaps: {len(cross_ref.identified_gaps)}")

    print("\\n🎯 Running Confidence Scoring...")
    confidence = pr_confidence_scorer.calculate_confidence_score(
        pr_data, jira_data, confluence_docs, {
            'overall_alignment_score': cross_ref.overall_alignment_score,
            'requirements_alignment': cross_ref.requirement_alignment,
            'documentation_consistency': cross_ref.documentation_consistency,
            'identified_gaps': cross_ref.identified_gaps
        }
    )
    print(f"   Score: {confidence.overall_score:.1%}")
    print(f"   Level: {confidence.confidence_level.value.upper()}")
    print(f"   Recommendation: {confidence.approval_recommendation.value.replace('_', ' ').title()}")

    print("\\n🔍 Running Gap Detection...")
    gaps = pr_gap_detector.detect_gaps(pr_data, jira_data, confluence_docs, {
        'identified_gaps': cross_ref.identified_gaps
    })
    gap_summary = pr_gap_detector.get_gap_summary(gaps)
    print(f"   Total Gaps: {gap_summary['total_gaps']}")
    print(f"   Blocking: {gap_summary['blocking_gaps']}")

    print("\\n✅ WORKFLOW TEST COMPLETED SUCCESSFULLY!")
    print("\\n📋 FINAL RESULTS:")
    print(f"   Confidence Score: {confidence.overall_score:.1%} ({confidence.confidence_level.value.upper()})")
    print(f"   Approval Recommendation: {confidence.approval_recommendation.value.replace('_', ' ').title()}")
    print(f"   Risk Level: {cross_ref.risk_assessment.upper()}")
    print(f"   Total Gaps: {gap_summary['total_gaps']}")

    # Save results
    results = {
        "workflow_test": "completed",
        "confidence_score": confidence.overall_score,
        "recommendation": confidence.approval_recommendation.value,
        "gaps_found": gap_summary['total_gaps'],
        "timestamp": datetime.now().isoformat()
    }

    with open("final_workflow_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\\n💾 Results saved to: final_workflow_test_results.json")

    return results

async def main():
    """Main test function."""
    await test_complete_workflow()

if __name__ == "__main__":
    asyncio.run(main())
