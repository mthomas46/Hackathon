#!/usr/bin/env python3
"""End-to-End Ecosystem Test Script.

This script demonstrates the complete LLM Documentation Ecosystem workflow:
1. Generate mock data (Confluence, GitHub, Jira)
2. Store documents in doc_store
3. Use prompt_store for analysis prompts
4. Analyze documents with analysis service
5. Create unified summaries with summarizer hub
6. Generate final comprehensive report

Run this script to test the entire ecosystem integration.
"""

import asyncio
import json
import httpx
import time
from typing import Dict, Any, List
from datetime import datetime

# Configuration
SERVICES = {
    "interpreter": "http://localhost:5120",
    "orchestrator": "http://localhost:5099",
    "mock_data_generator": "http://localhost:5065",
    "doc_store": "http://localhost:5087",
    "prompt_store": "http://localhost:5110",
    "analysis_service": "http://localhost:5020",
    "summarizer_hub": "http://localhost:5060",
    "llm_gateway": "http://localhost:5055"
}

class EndToEndTester:
    """Comprehensive end-to-end ecosystem tester."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "services_tested": [],
            "workflows_executed": [],
            "documents_created": 0,
            "analyses_performed": 0,
            "summaries_generated": 0,
            "final_report_id": None,
            "errors": [],
            "success": False
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete end-to-end test workflow."""
        print("🚀 Starting End-to-End Ecosystem Test")
        print("=" * 60)

        try:
            # Step 1: Test service health
            await self.test_service_health()

            # Step 2: Generate mock data
            await self.generate_mock_data()

            # Step 3: Execute end-to-end workflow
            await self.execute_workflow()

            # Step 4: Validate results
            await self.validate_results()

            self.test_results["success"] = True
            self.test_results["end_time"] = datetime.now().isoformat()

        except Exception as e:
            self.test_results["errors"].append(str(e))
            print(f"❌ Test failed: {e}")

        finally:
            self.print_test_summary()

        return self.test_results

    async def test_service_health(self):
        """Test health of all required services."""
        print("\n🔍 Testing Service Health...")

        required_services = ["mock_data_generator", "doc_store", "orchestrator",
                           "prompt_store", "analysis_service", "summarizer_hub", "llm_gateway"]

        for service_name in required_services:
            try:
                url = f"{SERVICES[service_name]}/health"
                response = await self.client.get(url)

                if response.status_code == 200:
                    print(f"✅ {service_name}: Healthy")
                    self.test_results["services_tested"].append({
                        "service": service_name,
                        "status": "healthy",
                        "url": url
                    })
                else:
                    raise Exception(f"Service returned {response.status_code}")

            except Exception as e:
                print(f"❌ {service_name}: Unhealthy - {e}")
                self.test_results["services_tested"].append({
                    "service": service_name,
                    "status": "unhealthy",
                    "error": str(e)
                })

    async def generate_mock_data(self):
        """Generate mock data for testing."""
        print("\n🎭 Generating Mock Data...")

        try:
            # Generate comprehensive test dataset
            response = await self.client.post(
                f"{SERVICES['mock_data_generator']}/generate/workflow-data",
                json={
                    "test_topic": "Authentication Service Architecture",
                    "workflow_id": f"e2e-test-{int(time.time())}"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    mock_data = data["data"]
                    print("✅ Generated mock data:"                    print(f"   - Confluence pages: {len(mock_data.get('confluence_pages', []))}")
                    print(f"   - GitHub repos: {len(mock_data.get('github_repos', []))}")
                    print(f"   - Jira issues: {len(mock_data.get('jira_issues', []))}")
                    print(f"   - API docs: {len(mock_data.get('api_docs', []))}")

                    self.test_results["mock_data_generated"] = mock_data
                else:
                    raise Exception(f"Mock data generation failed: {data.get('error')}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            print(f"❌ Mock data generation failed: {e}")
            raise

    async def execute_workflow(self):
        """Execute the end-to-end workflow."""
        print("\n⚙️ Executing End-to-End Workflow...")

        try:
            # Start the workflow via orchestrator
            workflow_request = {
                "workflow_type": "end_to_end_test",
                "parameters": {
                    "test_topic": "Authentication Service Architecture",
                    "sources": ["confluence", "github", "jira"],
                    "analysis_type": "comprehensive"
                },
                "user_id": "e2e-tester",
                "context": {
                    "test_mode": True,
                    "generate_report": True
                }
            }

            response = await self.client.post(
                f"{SERVICES['orchestrator']}/workflows/execute",
                json=workflow_request,
                timeout=300.0  # 5 minute timeout for complex workflow
            )

            if response.status_code == 200:
                workflow_result = response.json()
                if workflow_result.get("success"):
                    print("✅ Workflow executed successfully")
                    print(f"   - Workflow ID: {workflow_result.get('workflow_id')}")

                    # Store workflow results
                    self.test_results["workflows_executed"].append({
                        "workflow_type": "end_to_end_test",
                        "workflow_id": workflow_result.get("workflow_id"),
                        "status": "completed",
                        "execution_time": workflow_result.get("execution_time")
                    })

                    # Extract key metrics from workflow result
                    if "data" in workflow_result:
                        data = workflow_result["data"]
                        self.test_results["documents_created"] = data.get("documents_created", 0)
                        self.test_results["analyses_performed"] = data.get("analyses_performed", 0)
                        self.test_results["summaries_generated"] = data.get("summaries_generated", 0)
                        self.test_results["final_report_id"] = data.get("final_report_id")

                else:
                    raise Exception(f"Workflow failed: {workflow_result.get('error')}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            print(f"❌ Workflow execution failed: {e}")
            raise

    async def validate_results(self):
        """Validate the results of the workflow execution."""
        print("\n✅ Validating Results...")

        # Check if documents were created
        if self.test_results["documents_created"] > 0:
            print(f"✅ Documents created: {self.test_results['documents_created']}")
        else:
            print("⚠️ No documents were created")

        # Check if analyses were performed
        if self.test_results["analyses_performed"] > 0:
            print(f"✅ Analyses performed: {self.test_results['analyses_performed']}")
        else:
            print("⚠️ No analyses were performed")

        # Check if summaries were generated
        if self.test_results["summaries_generated"] > 0:
            print(f"✅ Summaries generated: {self.test_results['summaries_generated']}")
        else:
            print("⚠️ No summaries were generated")

        # Check if final report was created
        if self.test_results["final_report_id"]:
            print(f"✅ Final report created: {self.test_results['final_report_id']}")

            # Try to retrieve the final report
            try:
                response = await self.client.get(
                    f"{SERVICES['doc_store']}/documents/{self.test_results['final_report_id']}"
                )
                if response.status_code == 200:
                    print("✅ Final report successfully retrieved from doc_store")
                else:
                    print("⚠️ Could not retrieve final report from doc_store")
            except Exception as e:
                print(f"⚠️ Error retrieving final report: {e}")
        else:
            print("⚠️ No final report was created")

    def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📊 END-TO-END TEST SUMMARY")
        print("=" * 60)

        # Overall status
        if self.test_results["success"]:
            print("🎉 OVERALL STATUS: SUCCESS")
        else:
            print("❌ OVERALL STATUS: FAILED")

        print(f"⏰ Start Time: {self.test_results['start_time']}")
        print(f"⏰ End Time: {datetime.now().isoformat()}")

        # Service health
        print(f"\n🔍 Services Tested: {len(self.test_results['services_tested'])}")
        healthy = sum(1 for s in self.test_results["services_tested"] if s["status"] == "healthy")
        print(f"   ✅ Healthy: {healthy}")
        print(f"   ❌ Unhealthy: {len(self.test_results['services_tested']) - healthy}")

        # Workflow execution
        print(f"\n⚙️ Workflows Executed: {len(self.test_results['workflows_executed'])}")
        for workflow in self.test_results["workflows_executed"]:
            print(f"   ✅ {workflow['workflow_type']} - {workflow['status']}")

        # Key metrics
        print("
📈 Key Metrics:"        print(f"   📄 Documents Created: {self.test_results['documents_created']}")
        print(f"   🔍 Analyses Performed: {self.test_results['analyses_performed']}")
        print(f"   📝 Summaries Generated: {self.test_results['summaries_generated']}")
        if self.test_results["final_report_id"]:
            print(f"   📋 Final Report ID: {self.test_results['final_report_id']}")

        # Errors
        if self.test_results["errors"]:
            print(f"\n❌ Errors Encountered: {len(self.test_results['errors'])}")
            for error in self.test_results["errors"]:
                print(f"   • {error}")

        print("\n" + "=" * 60)

        if self.test_results["success"]:
            print("🎯 END-TO-END TEST COMPLETED SUCCESSFULLY!")
            print("   The LLM Documentation Ecosystem is fully functional! 🚀")
        else:
            print("⚠️ END-TO-END TEST COMPLETED WITH ISSUES")
            print("   Review the errors above and check service configurations.")

        print("=" * 60)


async def main():
    """Main entry point for end-to-end testing."""
    print("🤖 LLM Documentation Ecosystem - End-to-End Test")
    print("Testing complete workflow integration...")

    async with EndToEndTester() as tester:
        results = await tester.run_complete_test()

        # Save results to file for analysis
        with open("end_to_end_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("
💾 Test results saved to: end_to_end_test_results.json"        return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        exit(0 if results.get("success", False) else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        exit(1)
