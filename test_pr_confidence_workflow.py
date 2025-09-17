#!/usr/bin/env python3
"""
Test PR Confidence Analysis Workflow

This script demonstrates how to execute the PR confidence analysis workflow
using the orchestrator service with mock data.
"""

import asyncio
import json
import httpx
from datetime import datetime

# Configuration
ORCHESTRATOR_URL = "http://localhost:5099"
WORKFLOW_TYPE = "pr_confidence_analysis"

# Mock PR data for testing
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

async def test_pr_confidence_workflow():
    """Test the PR confidence analysis workflow."""
    print("🚀 Testing PR Confidence Analysis Workflow")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Check orchestrator health
            print("🔍 Checking orchestrator health...")
            health_response = await client.get(f"{ORCHESTRATOR_URL}/health")
            if health_response.status_code != 200:
                print(f"❌ Orchestrator not healthy: {health_response.status_code}")
                return

            print("✅ Orchestrator is healthy")

            # Execute PR confidence analysis workflow
            print("\n🎯 Executing PR Confidence Analysis Workflow...")
            workflow_request = {
                "workflow_type": WORKFLOW_TYPE,
                "parameters": {
                    "pr_data": MOCK_PR_DATA,
                    "analysis_scope": "comprehensive",
                    "confidence_threshold": 0.7
                },
                "user_id": "test-user-123",
                "correlation_id": f"pr-analysis-{int(datetime.now().timestamp())}"
            }

            workflow_response = await client.post(
                f"{ORCHESTRATOR_URL}/workflows/ai/{WORKFLOW_TYPE}",
                json=workflow_request,
                headers={"Content-Type": "application/json"}
            )

            if workflow_response.status_code == 200:
                result = workflow_response.json()
                print("✅ Workflow executed successfully!")

                # Extract and display key results
                if "data" in result and "full_state" in result["data"]:
                    workflow_state = result["data"]["full_state"]
                    context = workflow_state.get("context", {})

                    print("\n📊 ANALYSIS RESULTS")
                    print("-" * 30)

                    # Display confidence score
                    confidence = context.get("confidence_score", {})
                    if confidence:
                        score = confidence.get("overall_score", 0)
                        level = confidence.get("confidence_level", "unknown")
                        print(".1%"
                        print(f"Confidence Level: {level.upper()}")

                    # Display gaps and risks
                    gaps = context.get("gaps", [])
                    risks = context.get("risks", [])
                    recommendations = context.get("recommendations", [])

                    if gaps:
                        print(f"\n⚠️ Gaps Identified ({len(gaps)}):")
                        for gap in gaps:
                            print(f"  • {gap}")

                    if risks:
                        print(f"\n🚨 Risks Identified ({len(risks)}):")
                        for risk in risks:
                            print(f"  • {risk}")

                    if recommendations:
                        print(f"\n💡 Recommendations ({len(recommendations)}):")
                        for rec in recommendations:
                            print(f"  • {rec}")

                    # Display final report summary
                    final_report = context.get("final_report", {})
                    if final_report:
                        print("
📋 FINAL REPORT SUMMARY"                        print("-" * 25)
                        print(f"PR ID: {final_report.get('pr_id')}")
                        print(f"Jira Ticket: {final_report.get('jira_ticket')}")
                        print(f"Approval Recommendation: {final_report.get('approval_recommendation', 'unknown').replace('_', ' ').title()}")

                else:
                    print("⚠️ Workflow completed but no detailed results available")
                    print(f"Response: {json.dumps(result, indent=2)}")

            else:
                print(f"❌ Workflow execution failed: {workflow_response.status_code}")
                print(f"Error: {workflow_response.text}")

        except httpx.RequestError as e:
            print(f"❌ Request failed: {e}")
            print("\n💡 Make sure the orchestrator service is running:")
            print("   python services/orchestrator/main.py")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

async def demonstrate_workflow_with_mock_data():
    """Demonstrate the workflow with different mock scenarios."""
    print("\n🎭 Demonstrating with Different Mock Scenarios")
    print("=" * 50)

    scenarios = [
        {
            "name": "High Confidence PR",
            "pr_data": {
                **MOCK_PR_DATA,
                "title": "Add Unit Tests for Authentication Module",
                "description": "This PR adds comprehensive unit tests for the authentication module with 95% coverage."
            },
            "expected_confidence": "High"
        },
        {
            "name": "Medium Confidence PR",
            "pr_data": {
                **MOCK_PR_DATA,
                "title": "Refactor Authentication Logic",
                "description": "This PR refactors the authentication logic but may have some gaps in error handling."
            },
            "expected_confidence": "Medium"
        },
        {
            "name": "Low Confidence PR",
            "pr_data": {
                **MOCK_PR_DATA,
                "title": "Major Authentication Rewrite",
                "description": "This PR completely rewrites the authentication system with breaking changes."
            },
            "expected_confidence": "Low"
        }
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        for scenario in scenarios:
            print(f"\n🧪 Testing Scenario: {scenario['name']}")
            print(f"Expected Confidence: {scenario['expected_confidence']}")

            try:
                workflow_request = {
                    "workflow_type": WORKFLOW_TYPE,
                    "parameters": {
                        "pr_data": scenario["pr_data"],
                        "analysis_scope": "comprehensive"
                    },
                    "user_id": "test-user-123"
                }

                response = await client.post(
                    f"{ORCHESTRATOR_URL}/workflows/ai/{WORKFLOW_TYPE}",
                    json=workflow_request,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    workflow_state = result.get("data", {}).get("full_state", {})
                    context = workflow_state.get("context", {})
                    confidence = context.get("confidence_score", {})
                    score = confidence.get("overall_score", 0)

                    print(".1%"
                else:
                    print(f"❌ Failed: {response.status_code}")

            except Exception as e:
                print(f"❌ Error: {e}")

def print_usage_instructions():
    """Print usage instructions."""
    print("\n📖 USAGE INSTRUCTIONS")
    print("=" * 30)
    print("1. Start the orchestrator service:")
    print("   python services/orchestrator/main.py")
    print()
    print("2. Run this test:")
    print("   python test_pr_confidence_workflow.py")
    print()
    print("3. Check the results in the orchestrator logs")
    print()
    print("4. View stored documents in the doc_store:")
    print("   curl http://localhost:5087/documents/search?q=pr_confidence")
    print()
    print("5. Check notifications in the notification service")
    print("   curl http://localhost:5075/notifications")

async def main():
    """Main test function."""
    print_usage_instructions()

    # Test basic workflow execution
    await test_pr_confidence_workflow()

    # Demonstrate with different scenarios
    await demonstrate_workflow_with_mock_data()

    print("\n🎉 PR Confidence Analysis Workflow Testing Complete!")
    print("\n💡 Next Steps:")
    print("   1. Review the generated reports in doc_store")
    print("   2. Check notifications sent to stakeholders")
    print("   3. Analyze workflow execution logs")
    print("   4. Integrate with real GitHub, Jira, and Confluence services")

if __name__ == "__main__":
    asyncio.run(main())
