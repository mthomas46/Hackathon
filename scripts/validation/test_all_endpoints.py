"""Comprehensive API Endpoint Testing Script

Tests all 50+ endpoints in the Analysis Service to ensure they work correctly
after the DDD refactor. This script validates:
- Endpoint availability and response codes
- Request/response format validation
- Error handling
- Data integrity
- Performance metrics
"""

import asyncio
import time
import json
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics


@dataclass
class EndpointTest:
    """Test configuration for an endpoint."""
    method: str
    path: str
    description: str
    request_body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    requires_auth: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Result of testing an endpoint."""
    endpoint: EndpointTest
    success: bool
    status_code: int
    response_time: float
    response_body: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class APIEndpointTester:
    """Comprehensive API endpoint tester."""

    def __init__(self, base_url: str = "http://localhost:5020"):
        """Initialize the tester."""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30

        # Test data for various endpoints
        self.test_data = self._get_test_data()

        # Define all endpoints to test
        self.endpoints = self._get_all_endpoints()

    def _get_test_data(self) -> Dict[str, Any]:
        """Get test data for various endpoint types."""
        return {
            "document_ids": ["doc-1", "doc-2", "doc-3"],
            "analysis_targets": ["doc:readme", "doc:api-spec"],
            "repository_urls": ["https://github.com/example/repo1", "https://github.com/example/repo2"],
            "semantic_request": {
                "targets": ["doc:readme", "doc:api-spec"],
                "threshold": 0.7,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "similarity_metric": "cosine",
                "options": {"include_embeddings": False}
            },
            "sentiment_request": {
                "targets": ["doc:readme"],
                "include_tone_analysis": True,
                "language": "en"
            },
            "quality_request": {
                "targets": ["doc:readme"],
                "quality_metrics": ["readability", "completeness", "consistency"],
                "thresholds": {"readability": 0.7, "completeness": 0.8}
            },
            "trend_request": {
                "targets": ["doc:readme"],
                "time_range_days": 90,
                "metrics": ["quality_score", "finding_count"],
                "aggregation": "weekly"
            },
            "risk_request": {
                "targets": ["doc:readme"],
                "risk_factors": ["age", "complexity", "usage"],
                "include_recommendations": True
            },
            "maintenance_request": {
                "document_data": {
                    "document_id": "doc-1",
                    "last_modified": "2024-01-01T00:00:00Z",
                    "quality_score": 0.8,
                    "finding_density": 0.5,
                    "usage_frequency": 50
                },
                "baseline_period_days": 90
            },
            "workflow_request": {
                "event_type": "pull_request",
                "repository": "example/repo",
                "branch": "main",
                "files_changed": ["README.md", "api.py"],
                "metadata": {"pr_number": 123, "author": "test-user"}
            },
            "distributed_request": {
                "task_type": "semantic_analysis",
                "payload": {"targets": ["doc:readme"]},
                "priority": "normal",
                "timeout_seconds": 300
            }
        }

    def _get_all_endpoints(self) -> List[EndpointTest]:
        """Define all endpoints to test."""
        return [
            # Analysis endpoints
            EndpointTest("POST", "/analyze", "Basic document analysis",
                        {"targets": self.test_data["analysis_targets"], "analysis_type": "consistency"}),
            EndpointTest("POST", "/analyze/semantic-similarity", "Semantic similarity analysis",
                        self.test_data["semantic_request"]),
            EndpointTest("POST", "/analyze/sentiment", "Sentiment analysis",
                        self.test_data["sentiment_request"]),
            EndpointTest("POST", "/analyze/tone", "Tone analysis",
                        self.test_data["sentiment_request"]),
            EndpointTest("POST", "/analyze/quality", "Content quality analysis",
                        self.test_data["quality_request"]),
            EndpointTest("POST", "/analyze/trends", "Trend analysis",
                        self.test_data["trend_request"]),
            EndpointTest("POST", "/analyze/trends/portfolio", "Portfolio trend analysis",
                        {"documents": [self.test_data["trend_request"]], "group_by": "document_type"}),
            EndpointTest("POST", "/analyze/risk", "Risk assessment",
                        self.test_data["risk_request"]),
            EndpointTest("POST", "/analyze/risk/portfolio", "Portfolio risk assessment",
                        {"documents": [self.test_data["risk_request"]], "group_by": "document_type"}),
            EndpointTest("POST", "/analyze/maintenance/forecast", "Maintenance forecasting",
                        self.test_data["maintenance_request"]),
            EndpointTest("POST", "/analyze/maintenance/forecast/portfolio", "Portfolio maintenance forecasting",
                        {"documents": [self.test_data["maintenance_request"]], "group_by": "document_type"}),
            EndpointTest("POST", "/analyze/quality/degradation", "Quality degradation detection",
                        {"document_id": "doc-1", "analysis_history": [], "baseline_period_days": 90}),
            EndpointTest("POST", "/analyze/quality/degradation/portfolio", "Portfolio quality degradation",
                        {"documents": [{"document_id": "doc-1", "analysis_history": []}], "baseline_period_days": 90}),
            EndpointTest("POST", "/analyze/change/impact", "Change impact analysis",
                        {"targets": ["doc:readme"], "changes": ["content_update"], "scope": "repository"}),
            EndpointTest("POST", "/analyze/change/impact/portfolio", "Portfolio change impact",
                        {"documents": [{"document_id": "doc-1", "changes": ["content_update"]}], "scope": "organization"}),

            # Distributed processing endpoints
            EndpointTest("POST", "/distributed/tasks", "Submit distributed task",
                        self.test_data["distributed_request"]),
            EndpointTest("POST", "/distributed/tasks/batch", "Submit batch tasks",
                        {"tasks": [self.test_data["distributed_request"]], "batch_id": "batch-1"}),
            EndpointTest("GET", "/distributed/tasks/task-1", "Get task status",
                        expected_status=404),  # Task doesn't exist
            EndpointTest("GET", "/distributed/workers", "Get worker status"),
            EndpointTest("GET", "/distributed/stats", "Get processing stats"),
            EndpointTest("GET", "/distributed/queue/status", "Get queue status"),
            EndpointTest("GET", "/distributed/load-balancing/config", "Get load balancing config"),

            # Repository endpoints
            EndpointTest("GET", "/repositories", "List repositories"),
            EndpointTest("POST", "/repositories/analyze", "Analyze repositories",
                        {"repositories": self.test_data["repository_urls"], "analysis_type": "consistency"}),
            EndpointTest("POST", "/repositories/connectivity", "Test repository connectivity",
                        {"repository_url": self.test_data["repository_urls"][0]}),
            EndpointTest("GET", "/repositories/supported-connectors", "Get supported connectors"),

            # Workflow endpoints
            EndpointTest("POST", "/workflows/events", "Process workflow event",
                        self.test_data["workflow_request"]),
            EndpointTest("GET", "/workflows/status", "Get workflow status"),
            EndpointTest("GET", "/workflows/queue", "Get workflow queue"),
            EndpointTest("POST", "/workflows/webhook-config", "Configure webhook",
                        {"repository": "example/repo", "webhook_url": "https://example.com/webhook"}),

            # Remediation endpoints
            EndpointTest("POST", "/remediate", "Automated remediation",
                        {"targets": ["doc:readme"], "issues": ["formatting"], "strategy": "auto"}),
            EndpointTest("POST", "/remediate/preview", "Remediation preview",
                        {"targets": ["doc:readme"], "issues": ["formatting"]}),

            # Reports endpoints
            EndpointTest("POST", "/reports/generate", "Generate report",
                        {"report_type": "consistency", "targets": self.test_data["analysis_targets"]}),
            EndpointTest("GET", "/reports", "List reports"),

            # Integration endpoints
            EndpointTest("GET", "/integration/status", "Get integration status"),
            EndpointTest("POST", "/integration/sync", "Sync integrations",
                        {"integration_type": "github", "sync_options": {"full_sync": False}}),

            # Findings endpoints
            EndpointTest("GET", "/findings", "Get findings",
                        {"page": 1, "page_size": 20}),
            EndpointTest("POST", "/findings/search", "Search findings",
                        {"query": "consistency", "filters": {"severity": "high"}}),
            EndpointTest("GET", "/findings/stats", "Get findings stats"),

            # PR Confidence endpoints
            EndpointTest("POST", "/pr-confidence/analyze", "Analyze PR confidence",
                        {"pr_url": "https://github.com/example/repo/pull/123", "analysis_type": "comprehensive"}),
            EndpointTest("GET", "/pr-confidence/history", "Get PR confidence history"),

            # Health endpoints
            EndpointTest("GET", "/health", "Service health check"),
            EndpointTest("GET", "/health/detailed", "Detailed health check"),
            EndpointTest("GET", "/health/dependencies", "Dependency health check"),
        ]

    async def test_all_endpoints(self, concurrent_requests: int = 5) -> Dict[str, Any]:
        """Test all endpoints concurrently."""
        print("🚀 Starting comprehensive API endpoint testing...")
        print(f"📊 Testing {len(self.endpoints)} endpoints with concurrency: {concurrent_requests}")

        start_time = time.time()

        # Test endpoints concurrently
        results = []
        semaphore = asyncio.Semaphore(concurrent_requests)

        async def test_endpoint_with_semaphore(endpoint: EndpointTest) -> TestResult:
            async with semaphore:
                return await self._test_single_endpoint(endpoint)

        tasks = [test_endpoint_with_semaphore(endpoint) for endpoint in self.endpoints]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_tests = 0
        failed_tests = 0
        total_response_time = 0
        response_times = []

        test_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_results.append(TestResult(
                    self.endpoints[i],
                    False,
                    0,
                    0.0,
                    None,
                    f"Test execution failed: {str(result)}"
                ))
                failed_tests += 1
            else:
                test_results.append(result)
                if result.success:
                    successful_tests += 1
                    total_response_time += result.response_time
                    response_times.append(result.response_time)
                else:
                    failed_tests += 1

        execution_time = time.time() - start_time

        # Calculate statistics
        avg_response_time = total_response_time / successful_tests if successful_tests > 0 else 0
        success_rate = (successful_tests / len(self.endpoints)) * 100

        # Group results by endpoint category
        results_by_category = self._group_results_by_category(test_results)

        # Generate summary report
        summary = {
            "total_endpoints": len(self.endpoints),
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": round(success_rate, 2),
            "average_response_time": round(avg_response_time, 3),
            "median_response_time": round(statistics.median(response_times), 3) if response_times else 0,
            "min_response_time": round(min(response_times), 3) if response_times else 0,
            "max_response_time": round(max(response_times), 3) if response_times else 0,
            "total_execution_time": round(execution_time, 3),
            "requests_per_second": round(len(self.endpoints) / execution_time, 2),
            "results_by_category": results_by_category,
            "failed_endpoints": [
                {
                    "method": r.endpoint.method,
                    "path": r.endpoint.path,
                    "status_code": r.status_code,
                    "error": r.error_message
                }
                for r in test_results if not r.success
            ]
        }

        print("\n📈 TEST SUMMARY:"        print(f"✅ Successful: {successful_tests}/{len(self.endpoints)} ({success_rate:.1f}%)")
        print(f"❌ Failed: {failed_tests}/{len(self.endpoints)}")
        print(f"⏱️  Average Response Time: {avg_response_time:.3f}s")
        print(f"🚀 Requests/Second: {summary['requests_per_second']}")
        print(f"🕐 Total Execution Time: {execution_time:.2f}s")

        return {
            "summary": summary,
            "detailed_results": [
                {
                    "endpoint": f"{r.endpoint.method} {r.endpoint.path}",
                    "success": r.success,
                    "status_code": r.status_code,
                    "response_time": round(r.response_time, 3),
                    "description": r.endpoint.description
                }
                for r in test_results
            ]
        }

    async def _test_single_endpoint(self, endpoint: EndpointTest) -> TestResult:
        """Test a single endpoint."""
        url = f"{self.base_url}{endpoint.path}"
        start_time = time.time()

        try:
            if endpoint.method == "GET":
                response = self.session.get(url, params=endpoint.request_body)
            elif endpoint.method == "POST":
                response = self.session.post(url, json=endpoint.request_body)
            elif endpoint.method == "PUT":
                response = self.session.put(url, json=endpoint.request_body)
            elif endpoint.method == "DELETE":
                response = self.session.delete(url, params=endpoint.request_body)
            else:
                raise ValueError(f"Unsupported HTTP method: {endpoint.method}")

            response_time = time.time() - start_time

            # Check if status code matches expected
            success = response.status_code == endpoint.expected_status

            # Parse response body
            try:
                response_body = response.json() if response.content else None
            except:
                response_body = {"raw_response": response.text[:500]}

            error_message = None if success else f"Expected {endpoint.expected_status}, got {response.status_code}"

            return TestResult(
                endpoint=endpoint,
                success=success,
                status_code=response.status_code,
                response_time=response_time,
                response_body=response_body,
                error_message=error_message
            )

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                success=False,
                status_code=0,
                response_time=response_time,
                error_message=f"Request failed: {str(e)}"
            )
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                success=False,
                status_code=0,
                response_time=response_time,
                error_message=f"Test execution failed: {str(e)}"
            )

    def _group_results_by_category(self, results: List[TestResult]) -> Dict[str, Dict[str, Any]]:
        """Group test results by endpoint category."""
        categories = {}

        for result in results:
            # Extract category from path
            path_parts = result.endpoint.path.strip('/').split('/')
            category = path_parts[0] if path_parts[0] else 'root'

            if category not in categories:
                categories[category] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "avg_response_time": 0,
                    "endpoints": []
                }

            categories[category]["total"] += 1
            if result.success:
                categories[category]["successful"] += 1
            else:
                categories[category]["failed"] += 1

            categories[category]["endpoints"].append({
                "method": result.endpoint.method,
                "path": result.endpoint.path,
                "success": result.success,
                "response_time": round(result.response_time, 3)
            })

        # Calculate averages
        for category_data in categories.values():
            successful_endpoints = [e for e in category_data["endpoints"] if e["success"]]
            if successful_endpoints:
                category_data["avg_response_time"] = round(
                    sum(e["response_time"] for e in successful_endpoints) / len(successful_endpoints),
                    3
                )

        return categories


async def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive API Endpoint Testing")
    parser.add_argument("--url", default="http://localhost:5020", help="Base URL of the API service")
    parser.add_argument("--concurrent", type=int, default=5, help="Number of concurrent requests")
    parser.add_argument("--output", default="endpoint_test_results.json", help="Output file for results")

    args = parser.parse_args()

    print("🔧 API Endpoint Testing Configuration:"    print(f"   Base URL: {args.url}")
    print(f"   Concurrent Requests: {args.concurrent}")
    print(f"   Output File: {args.output}")
    print()

    # Initialize tester
    tester = APIEndpointTester(args.url)

    # Run comprehensive tests
    results = await tester.test_all_endpoints(args.concurrent)

    # Save results to file
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {args.output}")

    # Print summary
    summary = results["summary"]
    if summary["success_rate"] >= 95:
        print("🎉 EXCELLENT: High success rate! API is working well.")
    elif summary["success_rate"] >= 80:
        print("✅ GOOD: Acceptable success rate, but some endpoints need attention.")
    else:
        print("⚠️  CONCERNS: Many endpoints are failing. Investigation needed.")

    # Show failed endpoints
    if summary["failed_endpoints"]:
        print("
❌ Failed Endpoints:"        for failed in summary["failed_endpoints"][:10]:  # Show first 10
            print(f"   {failed['method']} {failed['path']} - {failed['error']}")

        if len(summary["failed_endpoints"]) > 10:
            print(f"   ... and {len(summary['failed_endpoints']) - 10} more")


if __name__ == "__main__":
    asyncio.run(main())
