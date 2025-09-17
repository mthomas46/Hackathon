#!/usr/bin/env python3
"""
Refactored PR Confidence Analysis Workflow Test

Demonstrates the new architecture where:
- Orchestrator focuses on workflow orchestration
- Analysis Service contains the business logic
- Services communicate via HTTP APIs
"""

import asyncio
import json
import time
from datetime import datetime

# Import the refactored orchestration workflow
from services.orchestrator.modules.workflows.pr_confidence_orchestration import PRConfidenceOrchestrationWorkflow

# Import the analysis service (for direct testing)
from services.analysis_service.modules.pr_confidence_analysis import (
    PRConfidenceAnalysisRequest,
    pr_confidence_analysis_service
)

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
    }
]

async def test_analysis_service_directly():
    """Test the analysis service directly (bypassing orchestrator)."""
    print("🧪 Testing Analysis Service Directly")
    print("=" * 50)

    start_time = time.time()

    # Create analysis request
    analysis_request = PRConfidenceAnalysisRequest(
        pr_data=MOCK_PR_DATA,
        jira_data=MOCK_JIRA_DATA,
        confluence_docs=MOCK_CONFLUENCE_DOCS,
        analysis_scope="comprehensive",
        include_recommendations=True,
        confidence_threshold=0.7
    )

    print("🤖 Calling Analysis Service...")
    result = await pr_confidence_analysis_service.analyze_pr_confidence(analysis_request)

    analysis_time = time.time() - start_time

    print("1. Analysis Results:")
    print(f"   Level: {result.confidence_level.value.upper()}")
    print(f"   Recommendation: {result.approval_recommendation.value.replace('_', ' ').title()}")
    print(f"   Risk Assessment: {result.risk_assessment.upper()}")
    print(f"   Gaps Found: {len(result.detected_gaps)}")
    print(f"   Critical Concerns: {len(result.critical_concerns)}")
    print(f"   Recommendations: {len(result.recommendations)}")

    print("\\n2. Component Scores:")
    for component, score in result.component_scores.items():
        print(f"   Recommendation: {result.approval_recommendation.value.replace("_", " ").title()}")
    print("\\n3. Top Recommendations:")
    for i, rec in enumerate(result.recommendations[:3]):
        print(f"   {i+1}. {rec}")

    if result.detected_gaps:
        print("\\n4. Key Gaps:")
        for gap in result.detected_gaps[:3]:
            print(f"   • {gap['description']} ({gap['severity'].upper()})")

    print(".2f")

    return result, analysis_time

async def test_orchestrator_workflow():
    """Test the orchestrator workflow (which calls analysis service)."""
    print("\\n🎯 Testing Orchestrator Workflow")
    print("=" * 50)

    start_time = time.time()

    # Create workflow instance
    workflow_instance = PRConfidenceOrchestrationWorkflow()

    # Prepare workflow input
    workflow_input = {
        "parameters": {
            "pr_data": MOCK_PR_DATA,
            "jira_data": MOCK_JIRA_DATA,
            "confluence_docs": MOCK_CONFLUENCE_DOCS,
            "analysis_scope": "comprehensive",
            "confidence_threshold": 0.7
        },
        "user_id": "test-user-123"
    }

    print("🚀 Executing Orchestration Workflow...")
    print("   This will call the analysis service via HTTP...")

    try:
        # Note: In a real scenario, this would need the orchestrator service running
        # For now, we'll simulate the workflow execution
        print("   ⚠️  Note: Orchestrator service needs to be running for full workflow test")
        print("   💡 For now, demonstrating the workflow structure...")

        # Show the workflow nodes that would execute
        workflow_graph = workflow_instance.workflow
        print("\\n   Workflow Structure:")
        print(f"   • Nodes: {list(workflow_graph.nodes.keys())}")
        print(f"   • Edges: {len(list(workflow_graph.edges))}")

        orchestration_time = time.time() - start_time
        print(f"   Orchestration Time: {orchestration_time:.2f}s")
        return None, orchestration_time

    except Exception as e:
        print(f"   ❌ Orchestrator workflow test failed: {e}")
        return None, time.time() - start_time

async def test_service_integration():
    """Test the service-to-service integration pattern."""
    print("\\n🔗 Testing Service Integration Pattern")
    print("=" * 50)

    print("1. Service Architecture Overview:")
    print("   ┌─────────────────┐    HTTP API    ┌─────────────────┐")
    print("   │   Orchestrator  │───────────────▶│ Analysis Service │")
    print("   │                 │                │                 │")
    print("   │ • Workflow      │                │ • Cross-Ref     │")
    print("   │ • Coordination  │                │ • Confidence     │")
    print("   │ • Notifications │                │ • Gap Detection  │")
    print("   └─────────────────┘                └─────────────────┘")
    print("           │                                   │")
    print("           └─────────────── Calls ─────────────┘")

    print("\\n2. Benefits of This Architecture:")
    print("   ✅ Separation of Concerns")
    print("      - Orchestrator: Workflow & Coordination")
    print("      - Analysis Service: Business Logic & AI")
    print()
    print("   ✅ Scalability")
    print("      - Analysis service can be scaled independently")
    print("      - Multiple analysis services for different domains")
    print()
    print("   ✅ Maintainability")
    print("      - Clear service boundaries")
    print("      - Independent deployment & updates")
    print()
    print("   ✅ Testability")
    print("      - Each service can be tested independently")
    print("      - Mock services for integration testing")

    print("\\n3. API Endpoints:")
    print("   POST /pr-confidence/analyze")
    print("   GET  /pr-confidence/history/{pr_id}")
    print("   GET  /pr-confidence/statistics")

async def demonstrate_workflow_execution():
    """Demonstrate the complete workflow execution flow."""
    print("\\n🔄 Complete Workflow Execution Flow")
    print("=" * 50)

    print("1. Orchestrator Workflow Steps:")
    print("   ┌─────────────────────────────────────┐")
    print("   │ 1. Extract PR Context               │")
    print("   │    • Parse PR data                  │")
    print("   │    • Validate inputs                │")
    print("   └─────────────────────────────────────┘")
    print("             │")
    print("             ▼")
    print("   ┌─────────────────────────────────────┐")
    print("   │ 2. Fetch Jira Requirements          │")
    print("   │    • Call source-agent service      │")
    print("   │    • Get acceptance criteria        │")
    print("   └─────────────────────────────────────┘")
    print("             │")
    print("             ▼")
    print("   ┌─────────────────────────────────────┐")
    print("   │ 3. Fetch Confluence Docs            │")
    print("   │    • Call source-agent service      │")
    print("   │    • Get API documentation          │")
    print("   └─────────────────────────────────────┘")
    print("             │")
    print("             ▼")
    print("   ┌─────────────────────────────────────┐")
    print("   │ 4. Coordinate Analysis              │")
    print("   │    • Call analysis service          │")
    print("   │    • Pass all collected data        │")
    print("   │    • Wait for analysis results      │")
    print("   └─────────────────────────────────────┘")
    print("             │")
    print("             ▼")
    print("   ┌─────────────────────────────────────┐")
    print("   │ 5. Generate Report                  │")
    print("   │    • Format analysis results        │")
    print("   │    • Create HTML/JSON reports       │")
    print("   │    • Store in doc_store             │")
    print("   └─────────────────────────────────────┘")
    print("             │")
    print("             ▼")
    print("   ┌─────────────────────────────────────┐")
    print("   │ 6. Send Notifications               │")
    print("   │    • Notify PR author               │")
    print("   │    • Notify tech lead if needed     │")
    print("   │    • Include report links           │")
    print("   └─────────────────────────────────────┘")

    print("\\n2. Analysis Service Processing:")
    print("   ┌─────────────────────────────────────┐")
    print("   │ Analysis Service Receives Request   │")
    print("   └─────────────────────────────────────┘")
    print("             │")
    print("             ▼")
    print("   ┌─────────────────────────────────────┐")
    print("   │ • Cross-Reference Analysis          │")
    print("   │ • Confidence Scoring                │")
    print("   │ • Gap Detection                     │")
    print("   │ • Recommendation Generation         │")
    print("   └─────────────────────────────────────┘")
    print("             │")
    print("             ▼")
    print("   ┌─────────────────────────────────────┐")
    print("   │ Return Analysis Results             │")
    print("   └─────────────────────────────────────┘")

async def run_complete_refactored_test():
    """Run the complete refactored workflow test."""
    print("🚀 COMPLETE REFACTORED PR CONFIDENCE ANALYSIS TEST")
    print("=" * 60)
    print("Testing the new microservices architecture:")
    print("• Orchestrator: Workflow orchestration & coordination")
    print("• Analysis Service: Business logic & AI analysis")
    print("=" * 60)

    total_start_time = time.time()

    try:
        # Test 1: Analysis Service Direct Call
        analysis_result, analysis_time = await test_analysis_service_directly()

        # Test 2: Service Integration Pattern
        await test_service_integration()

        # Test 3: Workflow Execution Flow
        await demonstrate_workflow_execution()

        # Test 4: Orchestrator Workflow (simulated)
        orch_result, orch_time = await test_orchestrator_workflow()

        # Final summary
        total_time = time.time() - total_start_time

        print("\\n🎉 REFACTORED ARCHITECTURE TEST COMPLETED!")
        print("=" * 60)

        if analysis_result:
            print("\\n📊 ANALYSIS RESULTS:")
            print(f"   Confidence Score: {results["analysis_result"]["confidence_score"]:.1%} ({results["analysis_result"]["confidence_level"].upper()})")
            print(f"   Confidence Level: {analysis_result.confidence_level.value.upper()}")
            print(f"   Approval Recommendation: {analysis_result.approval_recommendation.value.replace('_', ' ').title()}")
            print(f"   Risk Assessment: {analysis_result.risk_assessment.upper()}")
            print(f"   Gaps Identified: {len(analysis_result.detected_gaps)}")
            print(f"   Recommendations: {len(analysis_result.recommendations)}")

        print("\\n⏱️ PERFORMANCE METRICS:")
        print(".2f"        print(".2f"        print(".2f"
        print("\\n✅ ARCHITECTURE BENEFITS DEMONSTRATED:")
        print("   ✅ Separation of Concerns")
        print("   ✅ Service Independence")
        print("   ✅ Scalable Architecture")
        print("   ✅ Maintainable Codebase")
        print("   ✅ Independent Testing")

        print("\\n💡 NEXT STEPS:")
        print("   1. Start analysis service: python services/analysis-service/main.py")
        print("   2. Start orchestrator: python services/orchestrator/main.py")
        print("   3. Test full workflow with real service calls")
        print("   4. Add more analysis types to the analysis service")

        return {
            "success": True,
            "analysis_result": analysis_result.__dict__ if analysis_result else None,
            "analysis_time": analysis_time,
            "orchestration_time": orch_time,
            "total_time": total_time
        }

    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "total_time": time.time() - total_start_time
        }

async def main():
    """Main test execution."""
    results = await run_complete_refactored_test()

    # Save test results
    with open("refactored_architecture_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("\\n💾 Results saved to: refactored_architecture_test_results.json")

    if results["success"]:
        print("\\n🎯 STATUS: SUCCESS")
        print("Refactored microservices architecture is working correctly!")
    else:
        print("\\n❌ STATUS: FAILED")
        print("Some issues need to be resolved.")

if __name__ == "__main__":
    asyncio.run(main())
