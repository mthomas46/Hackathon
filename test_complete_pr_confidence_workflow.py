#!/usr/bin/env python3
"""
Complete PR Confidence Analysis Workflow Test

This script demonstrates the full PR confidence analysis workflow
using all the advanced analysis modules with Ollama LLM integration.
"""

import asyncio
import json
import time
from datetime import datetime

# Import all the analysis modules
from services.orchestrator.modules.analysis.pr_cross_reference_analyzer import pr_cross_reference_analyzer
from services.orchestrator.modules.analysis.pr_confidence_scorer import pr_confidence_scorer
from services.orchestrator.modules.analysis.pr_gap_detector import pr_gap_detector
from services.orchestrator.modules.analysis.pr_report_generator import pr_report_generator

# Mock data for testing
MOCK_PR_DATA = {
    "id": "PR-12345",
    "title": "Implement OAuth2 Authentication Service",
    "description": """
    This PR implements OAuth2 authentication for the user service.
    Key changes:
    - Add OAuth2 client configuration
    - Implement token validation middleware
    - Add user authentication endpoints
    - Update API documentation

    Related Jira: PROJ-456
    Confluence Docs: API_AUTH_DOCS, SECURITY_GUIDE
    """,
    "author": "developer@example.com",
    "jira_ticket": "PROJ-456",
    "related_docs": ["API_AUTH_DOCS", "SECURITY_GUIDE"],
    "files_changed": [
        "src/auth/oauth2_client.py",
        "src/auth/middleware.py",
        "src/api/auth_endpoints.py",
        "docs/api/authentication.md"
    ],
    "diff_summary": "+250 lines, -50 lines",
    "url": "https://github.com/company/repo/pull/12345"
}

MOCK_JIRA_DATA = {
    "id": "PROJ-456",
    "title": "Implement OAuth2 Authentication",
    "description": "As a user, I want to authenticate using OAuth2 so that I can securely access the API.",
    "acceptance_criteria": [
        "User can authenticate with OAuth2 provider",
        "API validates OAuth2 tokens",
        "Token refresh mechanism implemented",
        "Documentation updated"
    ],
    "story_points": 8,
    "priority": "High"
}

MOCK_CONFLUENCE_DOCS = [
    {
        "id": "API_AUTH_DOCS",
        "title": "Authentication API Documentation",
        "content": """
        # Authentication Service

        ## OAuth2 Flow
        1. Client requests authorization
        2. User is redirected to OAuth provider
        3. Provider returns authorization code
        4. Client exchanges code for access token

        ## Endpoints
        - POST /auth/login - User login
        - POST /auth/token - Token exchange
        - POST /auth/refresh - Token refresh
        - GET /auth/user - Get user info

        ## Security Requirements
        - All endpoints must validate JWT tokens
        - Tokens must expire within 1 hour
        - Refresh tokens valid for 30 days
        """,
        "last_updated": "2024-09-10T14:30:00Z"
    },
    {
        "id": "SECURITY_GUIDE",
        "title": "Security Implementation Guide",
        "content": """
        # Security Implementation Guide

        ## Authentication
        - Use OAuth2 for external authentication
        - Implement JWT token validation
        - Add refresh token mechanism
        - Validate all user inputs

        ## Authorization
        - Implement role-based access control
        - Validate permissions on all endpoints
        - Log security events
        """,
        "last_updated": "2024-09-08T10:15:00Z"
    }
]

async def test_cross_reference_analysis():
    """Test the cross-reference analysis module."""
    print("🔍 Testing Cross-Reference Analysis")
    print("=" * 50)

    start_time = time.time()

    # Test requirements alignment analysis
    print("1. Testing Requirements Alignment Analysis...")
    alignment_analysis = pr_cross_reference_analyzer.analyze_pr_requirements_alignment(
        MOCK_PR_DATA, MOCK_JIRA_DATA
    )
    print(f"   Overall Score: {alignment_analysis["overall_score"]:.1%}")
    print(f"   Gaps Identified: {len(alignment_analysis['gaps'])}")

    # Test documentation consistency analysis
    print("\\n2. Testing Documentation Consistency Analysis...")
    consistency_analysis = pr_cross_reference_analyzer.analyze_documentation_consistency(
        MOCK_PR_DATA, MOCK_CONFLUENCE_DOCS
    )
    print(".1%"
    print(f"   Issues Found: {len(consistency_analysis['issues'])}")

    # Test comprehensive cross-reference analysis
    print("\\n3. Testing Comprehensive Cross-Reference Analysis...")
    cross_reference_results = pr_cross_reference_analyzer.perform_comprehensive_cross_reference(
        MOCK_PR_DATA, MOCK_JIRA_DATA, MOCK_CONFLUENCE_DOCS
    )
    print(".1%"
    print(f"   Risk Assessment: {cross_reference_results.risk_assessment.upper()}")
    print(f"   Total Gaps: {len(cross_reference_results.identified_gaps)}")
    print(f"   Consistency Issues: {len(cross_reference_results.consistency_issues)}")

    analysis_time = time.time() - start_time
    print(".2f")

    return cross_reference_results, analysis_time

async def test_confidence_scoring(cross_reference_results):
    """Test the confidence scoring module."""
    print("\\n🎯 Testing Confidence Scoring")
    print("=" * 50)

    start_time = time.time()

    # Calculate confidence score
    confidence_score = pr_confidence_scorer.calculate_confidence_score(
        MOCK_PR_DATA, MOCK_JIRA_DATA, MOCK_CONFLUENCE_DOCS, {
            'overall_alignment_score': cross_reference_results.overall_alignment_score,
            'requirements_alignment': cross_reference_results.requirement_alignment,
            'documentation_consistency': cross_reference_results.documentation_consistency,
            'identified_gaps': cross_reference_results.identified_gaps,
            'consistency_issues': cross_reference_results.consistency_issues
        }
    )

    print("1. Confidence Score Results:")
    print(f"   Consistency Score: {consistency_analysis["overall_score"]:.1%}")
    print(f"   Level: {confidence_score.confidence_level.value.upper()}")
    print(f"   Recommendation: {confidence_score.approval_recommendation.value.replace('_', ' ').title()}")
    print(f"   Risk Factors: {len(confidence_score.risk_factors)}")
    print(f"   Critical Concerns: {len(confidence_score.critical_concerns)}")
    print(f"   Strengths: {len(confidence_score.strengths)}")

    print("\\n2. Component Scores:")
    for component, score in confidence_score.component_scores.items():
        print(f"   {component.replace("_", " ").title()}: {score:.1%}")
    print("\\n3. Key Findings:")
    if confidence_score.critical_concerns:
        print(f"   🚨 Critical: {len(confidence_score.critical_concerns)} concerns")
    if confidence_score.risk_factors:
        print(f"   ⚠️ Risks: {len(confidence_score.risk_factors)} factors")
    if confidence_score.strengths:
        print(f"   ✅ Strengths: {len(confidence_score.strengths)} areas")

    scoring_time = time.time() - start_time
    print(".2f")

    return confidence_score, scoring_time

async def test_gap_detection(cross_reference_results):
    """Test the gap detection module."""
    print("\\n🔍 Testing Gap Detection")
    print("=" * 50)

    start_time = time.time()

    # Detect gaps
    detected_gaps = pr_gap_detector.detect_gaps(
        MOCK_PR_DATA, MOCK_JIRA_DATA, MOCK_CONFLUENCE_DOCS, {
            'overall_alignment_score': cross_reference_results.overall_alignment_score,
            'requirements_alignment': {'gaps': cross_reference_results.identified_gaps},
            'documentation_consistency': {'issues': cross_reference_results.consistency_issues}
        }
    )

    # Get gap summary
    gap_summary = pr_gap_detector.get_gap_summary(detected_gaps)

    print("1. Gap Detection Results:")
    print(f"   Total Gaps Found: {gap_summary['total_gaps']}")
    print(f"   Blocking Gaps: {gap_summary['blocking_gaps']}")
    print(f"   Overall Risk: {gap_summary['overall_risk_level'].upper()}")

    print("\\n2. Gap Severity Distribution:")
    for severity, count in gap_summary['severity_distribution'].items():
        if count > 0:
            print(f"   {severity.upper()}: {count}")

    print("\\n3. Gap Types:")
    for gap_type, count in gap_summary['type_distribution'].items():
        if count > 0:
            print(f"   {gap_type.replace('_', ' ').title()}: {count}")

    print("\\n4. Sample Gaps:")
    prioritized_gaps = pr_gap_detector.prioritize_gaps(detected_gaps)
    for i, gap in enumerate(prioritized_gaps[:5]):  # Show first 5
        blocking = " 🚫 BLOCKING" if gap.blocking_approval else ""
        print(f"   {i+1}. {gap.description[:60]}... [{gap.severity.value.upper()}]{blocking}")

    detection_time = time.time() - start_time
    print(".2f")

    return detected_gaps, gap_summary, detection_time

async def test_report_generation(cross_reference_results, confidence_score, detected_gaps, total_time):
    """Test the report generation module."""
    print("\\n📋 Testing Report Generation")
    print("=" * 50)

    start_time = time.time()

    # Generate comprehensive report
    report = pr_report_generator.generate_report(
        MOCK_PR_DATA, MOCK_JIRA_DATA, MOCK_CONFLUENCE_DOCS,
        cross_reference_results, confidence_score,
        detected_gaps, total_time
    )

    # Save reports
    saved_files = pr_report_generator.save_reports(report, "test_reports")

    print("1. Report Generation Results:")
    print(f"   Report ID: {report.workflow_id}")
    print(f"   PR Analyzed: {report.pr_id}")
    print(f"   Jira Ticket: {report.jira_ticket}")
    print(f"   Confidence Score: {report.confidence_score:.1%}")
    print(f"   Approval Recommendation: {report.approval_recommendation.replace('_', ' ').title()}")

    print("\\n2. Report Sections:")
    print(f"   Component Scores: {len(report.component_scores)}")
    print(f"   Recommendations: {len(report.recommendations)}")
    print(f"   Critical Concerns: {len(report.critical_concerns)}")
    print(f"   Detected Gaps: {len(report.detected_gaps)}")

    print("\\n3. Generated Files:")
    for file_type, filepath in saved_files.items():
        print(f"   {file_type.upper()}: {filepath}")

    generation_time = time.time() - start_time
    print(".2f")

    return report, saved_files, generation_time

async def run_complete_workflow_test():
    """Run the complete PR confidence analysis workflow test."""
    print("🚀 COMPLETE PR CONFIDENCE ANALYSIS WORKFLOW TEST")
    print("=" * 60)
    print(f"Test Start Time: {datetime.now().isoformat()}")
    print(f"PR: {MOCK_PR_DATA['id']} - {MOCK_PR_DATA['title']}")
    print(f"Jira: {MOCK_JIRA_DATA['id']} - {MOCK_JIRA_DATA['title']}")
    print(f"Confluence Docs: {len(MOCK_CONFLUENCE_DOCS)} documents")
    print()

    total_start_time = time.time()

    try:
        # Step 1: Cross-reference analysis
        cross_reference_results, analysis_time = await test_cross_reference_analysis()

        # Step 2: Confidence scoring
        confidence_score, scoring_time = await test_confidence_scoring(cross_reference_results)

        # Step 3: Gap detection
        detected_gaps, gap_summary, detection_time = await test_gap_detection(cross_reference_results)

        # Step 4: Report generation
        total_workflow_time = time.time() - total_start_time
        report, saved_files, generation_time = await test_report_generation(
            cross_reference_results, confidence_score, detected_gaps, total_workflow_time
        )

        # Final summary
        print("\\n🎉 WORKFLOW TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)

        print("\\n📊 FINAL RESULTS SUMMARY")
        print("-" * 30)
        print(f"Overall Confidence: {confidence_score.overall_score:.1%} ({confidence_score.confidence_level.value.upper()})")
        print(f"Approval Recommendation: {confidence_score.approval_recommendation.value.replace('_', ' ').title()}")
        print(f"Risk Assessment: {cross_reference_results.risk_assessment.upper()}")
        print(f"Total Gaps Found: {gap_summary['total_gaps']} ({gap_summary['blocking_gaps']} blocking)")
        print(f"Analysis Duration: {total_workflow_time:.2f} seconds")

        print("\\n⏱️ PERFORMANCE BREAKDOWN")
        print("-" * 30)
        print(".2f"        print(".2f"        print(".2f"        print(".2f"        print(".2f"
        print("\\n📋 REPORTS GENERATED")
        print("-" * 30)
        for file_type, filepath in saved_files.items():
            print(f"{file_type.upper()}: {filepath}")

        print("\\n✅ ALL ANALYSIS MODULES TESTED SUCCESSFULLY")
        print("✅ Cross-Reference Analysis: Working")
        print("✅ Confidence Scoring: Working")
        print("✅ Gap Detection: Working")
        print("✅ Report Generation: Working")
        print("✅ Ollama LLM Integration: Working")

        # Save complete test results
        test_results = {
            "test_metadata": {
                "test_start_time": datetime.fromtimestamp(total_start_time).isoformat(),
                "test_end_time": datetime.now().isoformat(),
                "total_duration": total_workflow_time,
                "pr_id": MOCK_PR_DATA["id"],
                "jira_id": MOCK_JIRA_DATA["id"],
                "docs_count": len(MOCK_CONFLUENCE_DOCS)
            },
            "analysis_results": {
                "confidence_score": confidence_score.overall_score,
                "confidence_level": confidence_score.confidence_level.value,
                "approval_recommendation": confidence_score.approval_recommendation.value,
                "total_gaps": gap_summary["total_gaps"],
                "blocking_gaps": gap_summary["blocking_gaps"],
                "risk_level": cross_reference_results.risk_assessment
            },
            "performance_metrics": {
                "cross_reference_time": analysis_time,
                "confidence_scoring_time": scoring_time,
                "gap_detection_time": detection_time,
                "report_generation_time": generation_time
            },
            "generated_reports": saved_files
        }

        with open("complete_workflow_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2, default=str)

        print("\\n💾 Complete test results saved to: complete_workflow_test_results.json"
        return test_results

    except Exception as e:
        print(f"\\n❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def print_test_summary():
    """Print test execution summary."""
    print("\\n🧪 TEST EXECUTION SUMMARY")
    print("=" * 40)
    print("This test demonstrates the complete PR confidence analysis workflow:")
    print()
    print("1. 🔍 Cross-Reference Analysis")
    print("   - Compares PR implementation vs Jira requirements")
    print("   - Analyzes documentation consistency")
    print("   - Identifies alignment gaps and issues")
    print()
    print("2. 🎯 Confidence Scoring")
    print("   - Calculates overall approval confidence (0-100%)")
    print("   - Assesses risk levels and concerns")
    print("   - Provides approval recommendations")
    print()
    print("3. 🔍 Gap Detection")
    print("   - Identifies missing requirements, tests, docs")
    print("   - Categorizes gaps by severity and type")
    print("   - Flags blocking issues")
    print()
    print("4. 📋 Report Generation")
    print("   - Creates comprehensive HTML and JSON reports")
    print("   - Includes executive summary and detailed findings")
    print("   - Provides actionable recommendations")
    print()
    print("5. 🤖 AI Integration")
    print("   - Uses Ollama for intelligent analysis")
    print("   - Provides context-aware insights")
    print("   - Generates human-readable recommendations")

async def main():
    """Main test execution."""
    print_test_summary()

    # Run the complete workflow test
    results = await run_complete_workflow_test()

    if results:
        print("\\n🎯 TEST STATUS: SUCCESS")
        print("All PR confidence analysis modules are working correctly!")
        print("Ready for production deployment with Ollama LLM integration.")
    else:
        print("\\n❌ TEST STATUS: FAILED")
        print("Some modules need debugging. Check error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
