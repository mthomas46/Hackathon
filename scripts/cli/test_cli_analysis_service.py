#!/usr/bin/env python3
"""
Test suite for CLI Analysis Service functionality
Tests all new CLI commands against live services
"""

import os
import sys
import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.shared.integrations.clients.clients import ServiceClients
from services.shared.core.constants_new import ServiceNames


class CLIAnalysisServiceTester:
    """Test class for CLI Analysis Service functionality."""

    def __init__(self, base_url: str = "http://localhost:5020"):
        """Initialize tester with Analysis Service URL."""
        self.base_url = base_url.rstrip('/')
        self.clients = ServiceClients()
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.test_document_ids: List[str] = []

    async def setup_test_data(self):
        """Create test documents for analysis."""
        print("🔧 Setting up test data...")

        test_docs = [
            {
                "id": "test_doc_1",
                "content": "This is a test document about machine learning and AI technologies.",
                "metadata": {"type": "documentation", "category": "technical"}
            },
            {
                "id": "test_doc_2",
                "content": "Another test document covering cloud computing and DevOps practices.",
                "metadata": {"type": "documentation", "category": "infrastructure"}
            },
            {
                "id": "test_doc_3",
                "content": "Final test document discussing cybersecurity and data protection.",
                "metadata": {"type": "documentation", "category": "security"}
            }
        ]

        for doc in test_docs:
            try:
                # Try to create document via Doc Store first
                doc_store_url = f"{self.clients.doc_store_url()}/documents"
                response = await self.clients.post_json(doc_store_url, doc)
                if response and "id" in response:
                    self.test_document_ids.append(response["id"])
                    print(f"✅ Created test document: {response['id']}")
                else:
                    # Fallback to using test ID directly
                    self.test_document_ids.append(doc["id"])
                    print(f"⚠️ Using fallback test document: {doc['id']}")
            except Exception as e:
                print(f"⚠️ Could not create test document {doc['id']}: {e}")
                self.test_document_ids.append(doc["id"])

        print(f"📋 Test documents ready: {self.test_document_ids}")

    async def test_basic_analysis(self):
        """Test basic document analysis."""
        print("\n🧪 Testing basic document analysis...")

        try:
            url = f"{self.base_url}/analyze"
            payload = {
                "targets": [self.test_document_ids[0]],
                "analysis_type": "consistency"
            }
            response = await self.clients.post_json(url, payload)
            success = response and "findings" in response
            self.test_results["basic_analysis"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing findings in response"
            }
            print(f"✅ Basic analysis: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["basic_analysis"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ Basic analysis: FAIL - {e}")

    async def test_semantic_similarity(self):
        """Test semantic similarity analysis."""
        print("\n🧪 Testing semantic similarity analysis...")

        try:
            url = f"{self.base_url}/analyze/semantic-similarity"
            payload = {
                "targets": self.test_document_ids[:2],
                "threshold": 0.7
            }
            response = await self.clients.post_json(url, payload)
            success = response and "results" in response
            self.test_results["semantic_similarity"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing results in response"
            }
            print(f"✅ Semantic similarity: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["semantic_similarity"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ Semantic similarity: FAIL - {e}")

    async def test_sentiment_analysis(self):
        """Test sentiment analysis."""
        print("\n🧪 Testing sentiment analysis...")

        try:
            url = f"{self.base_url}/analyze/sentiment"
            payload = {"targets": self.test_document_ids}
            response = await self.clients.post_json(url, payload)
            success = response and "results" in response
            self.test_results["sentiment_analysis"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing results in response"
            }
            print(f"✅ Sentiment analysis: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["sentiment_analysis"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ Sentiment analysis: FAIL - {e}")

    async def test_quality_analysis(self):
        """Test content quality analysis."""
        print("\n🧪 Testing quality analysis...")

        try:
            url = f"{self.base_url}/analyze/quality"
            payload = {"targets": self.test_document_ids}
            response = await self.clients.post_json(url, payload)
            success = response and "results" in response
            self.test_results["quality_analysis"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing results in response"
            }
            print(f"✅ Quality analysis: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["quality_analysis"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ Quality analysis: FAIL - {e}")

    async def test_trend_analysis(self):
        """Test trend analysis."""
        print("\n🧪 Testing trend analysis...")

        try:
            url = f"{self.base_url}/analyze/trends"
            payload = {
                "targets": self.test_document_ids,
                "timeframe_days": 30
            }
            response = await self.clients.post_json(url, payload)
            success = response and "results" in response
            self.test_results["trend_analysis"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing results in response"
            }
            print(f"✅ Trend analysis: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["trend_analysis"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ Trend analysis: FAIL - {e}")

    async def test_risk_assessment(self):
        """Test risk assessment."""
        print("\n🧪 Testing risk assessment...")

        try:
            url = f"{self.base_url}/analyze/risk"
            payload = {"targets": self.test_document_ids}
            response = await self.clients.post_json(url, payload)
            success = response and "results" in response
            self.test_results["risk_assessment"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing results in response"
            }
            print(f"✅ Risk assessment: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["risk_assessment"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ Risk assessment: FAIL - {e}")

    async def test_remediation(self):
        """Test remediation suggestions."""
        print("\n🧪 Testing remediation...")

        try:
            url = f"{self.base_url}/remediate"
            payload = {
                "targets": [self.test_document_ids[0]],
                "issue_type": "quality"
            }
            response = await self.clients.post_json(url, payload)
            success = response and "remediation_plan" in response
            self.test_results["remediation"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing remediation_plan in response"
            }
            print(f"✅ Remediation: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["remediation"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ Remediation: FAIL - {e}")

    async def test_workflow_events(self):
        """Test workflow events."""
        print("\n🧪 Testing workflow events...")

        try:
            url = f"{self.base_url}/workflows/events"
            payload = {
                "event_type": "pr.created",
                "entity_type": "pr",
                "entity_id": "test-pr-123",
                "metadata": {"source": "cli-test"}
            }
            response = await self.clients.post_json(url, payload)
            success = response and "workflow_id" in response
            self.test_results["workflow_events"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing workflow_id in response"
            }
            print(f"✅ Workflow events: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["workflow_events"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ Workflow events: FAIL - {e}")

    async def test_distributed_processing(self):
        """Test distributed processing."""
        print("\n🧪 Testing distributed processing...")

        try:
            url = f"{self.base_url}/distributed/tasks"
            payload = {
                "task_type": "analysis",
                "targets": [self.test_document_ids[0]],
                "priority": "normal"
            }
            response = await self.clients.post_json(url, payload)
            success = response and "task_id" in response
            self.test_results["distributed_processing"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing task_id in response"
            }
            print(f"✅ Distributed processing: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["distributed_processing"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ Distributed processing: FAIL - {e}")

    async def test_report_generation(self):
        """Test report generation."""
        print("\n🧪 Testing report generation...")

        try:
            url = f"{self.base_url}/reports/generate"
            payload = {
                "kind": "summary",
                "format": "json"
            }
            response = await self.clients.post_json(url, payload)
            success = response and "report_id" in response
            self.test_results["report_generation"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing report_id in response"
            }
            print(f"✅ Report generation: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["report_generation"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ Report generation: FAIL - {e}")

    async def test_findings_and_detectors(self):
        """Test findings and detectors listing."""
        print("\n🧪 Testing findings and detectors...")

        # Test findings
        try:
            url = f"{self.base_url}/findings"
            response = await self.clients.get_json(url)
            findings_success = response and "findings" in response
        except Exception as e:
            findings_success = False
            print(f"⚠️ Findings test error: {e}")

        # Test detectors
        try:
            url = f"{self.base_url}/detectors"
            response = await self.clients.get_json(url)
            detectors_success = response and "detectors" in response
        except Exception as e:
            detectors_success = False
            print(f"⚠️ Detectors test error: {e}")

        success = findings_success and detectors_success
        self.test_results["findings_and_detectors"] = {
            "success": success,
            "findings_success": findings_success,
            "detectors_success": detectors_success,
            "error": None if success else "One or more endpoints failed"
        }
        print(f"✅ Findings & Detectors: {'PASS' if success else 'FAIL'}")

    async def test_integration_endpoints(self):
        """Test integration endpoints."""
        print("\n🧪 Testing integration endpoints...")

        # Test integration health
        try:
            url = f"{self.base_url}/integration/health"
            response = await self.clients.get_json(url)
            health_success = response and "status" in response
        except Exception as e:
            health_success = False
            print(f"⚠️ Integration health test error: {e}")

        # Test natural language analysis
        try:
            url = f"{self.base_url}/integration/natural-language-analysis"
            payload = {
                "query": "analyze the quality of these documents",
                "context": {"document_ids": self.test_document_ids}
            }
            response = await self.clients.post_json(url, payload)
            nlp_success = response and "results" in response
        except Exception as e:
            nlp_success = False
            print(f"⚠️ NLP analysis test error: {e}")

        success = health_success and nlp_success
        self.test_results["integration_endpoints"] = {
            "success": success,
            "health_success": health_success,
            "nlp_success": nlp_success,
            "error": None if success else "One or more integration endpoints failed"
        }
        print(f"✅ Integration endpoints: {'PASS' if success else 'FAIL'}")

    async def test_pr_confidence(self):
        """Test PR confidence analysis."""
        print("\n🧪 Testing PR confidence analysis...")

        try:
            url = f"{self.base_url}/pr-confidence/analyze"
            payload = {
                "pr_id": "test-pr-123",
                "analysis_type": "quick"
            }
            response = await self.clients.post_json(url, payload)
            success = response and "confidence_score" in response
            self.test_results["pr_confidence"] = {
                "success": success,
                "response": response,
                "error": None if success else "Missing confidence_score in response"
            }
            print(f"✅ PR confidence: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            self.test_results["pr_confidence"] = {
                "success": False,
                "response": None,
                "error": str(e)
            }
            print(f"❌ PR confidence: FAIL - {e}")

    async def run_all_tests(self):
        """Run all CLI analysis service tests."""
        print("🚀 CLI Analysis Service Test Suite")
        print("=" * 50)

        # Setup test data
        await self.setup_test_data()

        # Run all tests
        await self.test_basic_analysis()
        await self.test_semantic_similarity()
        await self.test_sentiment_analysis()
        await self.test_quality_analysis()
        await self.test_trend_analysis()
        await self.test_risk_assessment()
        await self.test_remediation()
        await self.test_workflow_events()
        await self.test_distributed_processing()
        await self.test_report_generation()
        await self.test_findings_and_detectors()
        await self.test_integration_endpoints()
        await self.test_pr_confidence()

        # Generate summary
        self.generate_test_summary()

    def generate_test_summary(self):
        """Generate and display test summary."""
        print("\n" + "=" * 50)
        print("📊 CLI ANALYSIS SERVICE TEST SUMMARY")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(".1f")

        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result["success"]:
                    print(f"  - {test_name}: {result.get('error', 'Unknown error')}")
        else:
            print("\n🎉 ALL TESTS PASSED!")

        # Save results to file
        results_file = project_root / "scripts" / "test" / "cli_analysis_service_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        print(f"\n📄 Detailed results saved to: {results_file}")


async def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="CLI Analysis Service Test Suite")
    parser.add_argument("--url", default="http://localhost:5020",
                       help="Analysis Service URL (default: http://localhost:5020)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        print(f"🔗 Testing against: {args.url}")

    tester = CLIAnalysisServiceTester(args.url)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
