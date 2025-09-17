#!/usr/bin/env python3
# =============================================================================
# API COMPATIBILITY VALIDATION SCRIPT
# =============================================================================
# Validates that all 53 legacy endpoints work correctly with the new DDD architecture
# Ensures 100% backward compatibility for existing clients

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
import httpx
import time
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CompatibilityTestResult:
    """Result of a compatibility test."""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    compatible: bool
    error_message: Optional[str] = None
    deprecation_warning: bool = False
    response_format_valid: bool = True

@dataclass
class CompatibilityTestSuite:
    """Test suite for API compatibility validation."""
    base_url: str
    results: List[CompatibilityTestResult] = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0

    def __post_init__(self):
        if self.results is None:
            self.results = []

    def add_result(self, result: CompatibilityTestResult):
        """Add a test result."""
        self.results.append(result)
        self.total_tests += 1
        if result.compatible:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary."""
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": f"{(self.passed_tests / self.total_tests * 100):.1f}%" if self.total_tests > 0 else "0%",
            "compatibility_status": "✅ FULLY COMPATIBLE" if self.failed_tests == 0 else "❌ ISSUES FOUND"
        }

class APICompatibilityValidator:
    """Validates API compatibility between legacy and DDD implementations."""

    def __init__(self, base_url: str = "http://localhost:5020"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_suite = CompatibilityTestSuite(base_url)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def get_legacy_endpoints(self) -> List[Dict[str, Any]]:
        """Get all legacy endpoints to test."""
        return [
            # Core Analysis Endpoints
            {"method": "POST", "path": "/analyze", "description": "Document consistency analysis"},
            {"method": "POST", "path": "/analyze/semantic-similarity", "description": "Semantic similarity analysis"},
            {"method": "POST", "path": "/analyze/sentiment", "description": "Sentiment analysis"},
            {"method": "POST", "path": "/analyze/tone", "description": "Tone analysis"},
            {"method": "POST", "path": "/analyze/quality", "description": "Content quality assessment"},
            {"method": "POST", "path": "/analyze/trends", "description": "Trend analysis"},
            {"method": "POST", "path": "/analyze/trends/portfolio", "description": "Portfolio trend analysis"},
            {"method": "POST", "path": "/analyze/risk", "description": "Risk assessment"},
            {"method": "POST", "path": "/analyze/risk/portfolio", "description": "Portfolio risk assessment"},
            {"method": "POST", "path": "/analyze/maintenance/forecast", "description": "Maintenance forecast"},
            {"method": "POST", "path": "/analyze/maintenance/forecast/portfolio", "description": "Portfolio maintenance forecast"},
            {"method": "POST", "path": "/analyze/quality/degradation", "description": "Quality degradation detection"},
            {"method": "POST", "path": "/analyze/quality/degradation/portfolio", "description": "Portfolio quality degradation"},
            {"method": "POST", "path": "/analyze/change/impact", "description": "Change impact analysis"},
            {"method": "POST", "path": "/analyze/change/impact/portfolio", "description": "Portfolio change impact analysis"},

            # Distributed Processing Endpoints
            {"method": "POST", "path": "/distributed/tasks", "description": "Submit distributed task"},
            {"method": "POST", "path": "/distributed/tasks/batch", "description": "Submit batch tasks"},
            {"method": "GET", "path": "/distributed/tasks/test-task-123", "description": "Get task status"},
            {"method": "DELETE", "path": "/distributed/tasks/test-task-123", "description": "Cancel task"},
            {"method": "GET", "path": "/distributed/workers", "description": "Get workers status"},
            {"method": "GET", "path": "/distributed/stats", "description": "Get processing stats"},
            {"method": "POST", "path": "/distributed/workers/scale", "description": "Scale workers"},
            {"method": "POST", "path": "/distributed/start", "description": "Start distributed processing"},
            {"method": "PUT", "path": "/distributed/load-balancing/strategy", "description": "Set load balancing strategy"},
            {"method": "GET", "path": "/distributed/queue/status", "description": "Get queue status"},
            {"method": "PUT", "path": "/distributed/load-balancing/config", "description": "Configure load balancing"},
            {"method": "GET", "path": "/distributed/load-balancing/config", "description": "Get load balancing config"},

            # Repository Management Endpoints
            {"method": "POST", "path": "/repositories/analyze", "description": "Analyze repositories"},
            {"method": "POST", "path": "/repositories/connectivity", "description": "Test repository connectivity"},
            {"method": "POST", "path": "/repositories/connectors/config", "description": "Configure connector"},
            {"method": "GET", "path": "/repositories/connectors", "description": "Get supported connectors"},
            {"method": "GET", "path": "/repositories/frameworks", "description": "Get analysis frameworks"},

            # Workflow Endpoints
            {"method": "POST", "path": "/workflows/events", "description": "Process workflow event"},
            {"method": "GET", "path": "/workflows/test-workflow-123", "description": "Get workflow status"},
            {"method": "GET", "path": "/workflows/queue/status", "description": "Get workflow queue status"},
            {"method": "POST", "path": "/workflows/webhook/config", "description": "Configure webhook"},

            # Remediation Endpoints
            {"method": "POST", "path": "/remediate", "description": "Automated remediation"},
            {"method": "POST", "path": "/remediate/preview", "description": "Remediation preview"},

            # Reporting Endpoints
            {"method": "POST", "path": "/reports/generate", "description": "Generate report"},
            {"method": "GET", "path": "/findings", "description": "Get findings"},
            {"method": "GET", "path": "/detectors", "description": "List detectors"},
            {"method": "GET", "path": "/reports/confluence/consolidation", "description": "Confluence consolidation"},
            {"method": "GET", "path": "/reports/jira/staleness", "description": "Jira staleness report"},
            {"method": "POST", "path": "/reports/findings/notify-owners", "description": "Notify owners"},

            # Integration Endpoints
            {"method": "GET", "path": "/integration/health", "description": "Integration health"},
            {"method": "POST", "path": "/integration/analyze-with-prompt", "description": "Analyze with prompt"},
            {"method": "POST", "path": "/integration/natural-language-analysis", "description": "Natural language analysis"},
            {"method": "GET", "path": "/integration/prompts/categories", "description": "Get prompt categories"},
            {"method": "POST", "path": "/integration/log-analysis", "description": "Log analysis"},
            {"method": "POST", "path": "/architecture/analyze", "description": "Architecture analysis"},

            # PR Confidence Endpoints
            {"method": "POST", "path": "/pr-confidence/analyze", "description": "Analyze PR confidence"},
            {"method": "GET", "path": "/pr-confidence/history/test-pr-123", "description": "Get PR history"},
            {"method": "GET", "path": "/pr-confidence/statistics", "description": "Get PR statistics"},
        ]

    def get_sample_payload(self, endpoint: str) -> Dict[str, Any]:
        """Get sample payload for endpoint testing."""
        payloads = {
            "/analyze": {
                "targets": ["doc:sample"],
                "analysis_type": "consistency"
            },
            "/analyze/semantic-similarity": {
                "documents": ["Sample document content"],
                "threshold": 0.7
            },
            "/analyze/sentiment": {
                "text": "This is a great feature that works well.",
                "context": "documentation"
            },
            "/analyze/tone": {
                "content": "This documentation is excellent.",
                "audience": "developers"
            },
            "/analyze/quality": {
                "document_id": "doc:sample",
                "content": "Sample documentation content for quality analysis."
            },
            "/analyze/trends": {
                "timeframe": "30d",
                "metrics": ["quality", "consistency"]
            },
            "/analyze/risk": {
                "document_id": "doc:sample",
                "factors": ["age", "complexity", "usage"]
            },
            "/distributed/tasks": {
                "task_type": "analysis",
                "payload": {"document_id": "doc:sample"},
                "priority": "normal"
            },
            "/distributed/tasks/batch": {
                "tasks": [
                    {
                        "task_type": "analysis",
                        "payload": {"document_id": "doc:1"}
                    }
                ]
            },
            "/repositories/analyze": {
                "repository_url": "https://github.com/example/repo",
                "analysis_type": "consistency"
            },
            "/repositories/connectivity": {
                "repository_url": "https://github.com/example/repo",
                "connection_type": "git"
            },
            "/workflows/events": {
                "event_type": "pr_opened",
                "payload": {"pr_id": "123", "repository": "example/repo"}
            },
            "/remediate": {
                "document_id": "doc:sample",
                "issues": [{"type": "grammar", "location": "line 10"}]
            },
            "/reports/generate": {
                "report_type": "consistency",
                "filters": {"severity": "high"}
            },
            "/integration/analyze-with-prompt": {
                "prompt": "Analyze this documentation",
                "context": "Sample documentation content"
            },
            "/pr-confidence/analyze": {
                "pr_id": "123",
                "repository": "example/repo",
                "changes": ["Modified README.md"]
            }
        }

        # Return default payload for endpoints without specific samples
        return payloads.get(endpoint, {"test": True})

    async def test_endpoint_compatibility(self, endpoint_info: Dict[str, Any]) -> CompatibilityTestResult:
        """Test compatibility of a single endpoint."""
        method = endpoint_info["method"]
        path = endpoint_info["path"]
        description = endpoint_info["description"]
        url = f"{self.base_url}{path}"

        start_time = time.time()

        try:
            # Prepare request
            payload = self.get_sample_payload(path) if method in ["POST", "PUT"] else None
            headers = {"Content-Type": "application/json"} if payload else {}

            # Make request
            if method == "GET":
                response = await self.client.get(url, headers=headers)
            elif method == "POST":
                response = await self.client.post(url, json=payload, headers=headers)
            elif method == "PUT":
                response = await self.client.put(url, json=payload, headers=headers)
            elif method == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response_time = time.time() - start_time

            # Validate response
            compatible = self.validate_response(response, endpoint_info)
            deprecation_warning = self.check_deprecation_warning(response)

            return CompatibilityTestResult(
                endpoint=path,
                method=method,
                status_code=response.status_code,
                response_time=response_time,
                compatible=compatible,
                deprecation_warning=deprecation_warning
            )

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Error testing {method} {path}: {e}")
            return CompatibilityTestResult(
                endpoint=path,
                method=method,
                status_code=0,
                response_time=response_time,
                compatible=False,
                error_message=str(e)
            )

    def validate_response(self, response: httpx.Response, endpoint_info: Dict[str, Any]) -> bool:
        """Validate that response maintains backward compatibility."""
        try:
            # Check status code
            if response.status_code not in [200, 201, 202, 400, 404, 422, 500]:
                logger.warning(f"Unexpected status code {response.status_code} for {endpoint_info['path']}")
                return False

            # Try to parse JSON response
            try:
                data = response.json()
            except:
                # Some endpoints might return non-JSON (like health checks)
                if endpoint_info["path"] in ["/health", "/integration/health"]:
                    return response.status_code == 200
                return False

            # Check for compatibility metadata
            if "_compatibility" not in data:
                logger.warning(f"Missing compatibility metadata in response for {endpoint_info['path']}")
                return False

            # Validate compatibility structure
            compatibility = data["_compatibility"]
            required_fields = ["version", "ddd_backend", "maintained_until"]
            for field in required_fields:
                if field not in compatibility:
                    logger.warning(f"Missing required compatibility field '{field}' in {endpoint_info['path']}")
                    return False

            # Check warnings array
            if "warnings" not in data:
                logger.warning(f"Missing warnings array in response for {endpoint_info['path']}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating response for {endpoint_info['path']}: {e}")
            return False

    def check_deprecation_warning(self, response: httpx.Response) -> bool:
        """Check if response contains deprecation warning."""
        try:
            data = response.json()
            warnings = data.get("warnings", [])
            return any(w.get("type") == "deprecation" for w in warnings)
        except:
            return False

    async def run_compatibility_tests(self) -> Dict[str, Any]:
        """Run all compatibility tests."""
        logger.info("🧪 Starting API Compatibility Validation Tests")
        logger.info(f"📍 Testing against: {self.base_url}")
        logger.info("=" * 60)

        endpoints = self.get_legacy_endpoints()
        logger.info(f"🎯 Testing {len(endpoints)} legacy endpoints")

        # Run tests concurrently with semaphore for rate limiting
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

        async def test_with_semaphore(endpoint_info):
            async with semaphore:
                return await self.test_endpoint_compatibility(endpoint_info)

        # Run all tests
        tasks = [test_with_semaphore(endpoint) for endpoint in endpoints]
        results = await asyncio.gather(*tasks)

        # Process results
        for result in results:
            self.test_suite.add_result(result)

            status_icon = "✅" if result.compatible else "❌"
            warning_icon = "⚠️" if result.deprecation_warning else ""
            time_str = ".2f"

            logger.info("2s")

            if not result.compatible and result.error_message:
                logger.error(f"   💥 Error: {result.error_message}")

        # Generate summary
        summary = self.test_suite.get_summary()
        logger.info("\n" + "=" * 60)
        logger.info("📊 COMPATIBILITY TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"🎯 Total Tests: {summary['total_tests']}")
        logger.info(f"✅ Passed: {summary['passed_tests']}")
        logger.info(f"❌ Failed: {summary['failed_tests']}")
        logger.info(f"📈 Success Rate: {summary['success_rate']}")
        logger.info(f"🏆 Status: {summary['compatibility_status']}")

        # Detailed results
        if summary['failed_tests'] > 0:
            logger.warning("\n🚨 FAILED ENDPOINTS:")
            for result in self.test_suite.results:
                if not result.compatible:
                    logger.warning(f"   • {result.method} {result.endpoint}")

        # Performance summary
        response_times = [r.response_time for r in self.test_suite.results if r.response_time > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            logger.info(f"⚡ Average Response Time: {avg_time:.2f}s")
            logger.info(f"🐌 Max Response Time: {max_time:.2f}s")
        return {
            "summary": summary,
            "results": [vars(result) for result in self.test_suite.results],
            "performance": {
                "average_response_time": avg_time if response_times else 0,
                "max_response_time": max_time if response_times else 0,
                "total_endpoints_tested": len(endpoints)
            }
        }

    def save_results(self, results: Dict[str, Any], output_file: str = "api_compatibility_results.json"):
        """Save test results to file."""
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"💾 Results saved to: {output_path}")

async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="API Compatibility Validation")
    parser.add_argument("--url", default="http://localhost:5020", help="Base URL of the Analysis Service")
    parser.add_argument("--output", default="api_compatibility_results.json", help="Output file for results")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("🚀 API Compatibility Validator")
    logger.info("🔧 Domain-Driven Design Transition Testing")
    logger.info("=" * 50)

    async with APICompatibilityValidator(args.url) as validator:
        results = await validator.run_compatibility_tests()
        validator.save_results(results, args.output)

        # Exit with appropriate code
        success_rate = float(results["summary"]["success_rate"].rstrip("%"))
        exit_code = 0 if success_rate == 100.0 else 1

        logger.info(f"\n🎯 Exit Code: {exit_code} ({'SUCCESS' if exit_code == 0 else 'ISSUES FOUND'})")
        return exit_code

if __name__ == "__main__":
    exit(asyncio.run(main()))
