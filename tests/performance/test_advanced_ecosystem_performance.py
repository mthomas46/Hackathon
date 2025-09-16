"""Performance tests for the advanced prompt ecosystem."""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import uuid
from typing import List, Dict, Any

from services.prompt_store.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create test client for performance testing."""
    return TestClient(app)


class PerformanceTestSuite:
    """Suite for running performance tests on the advanced ecosystem."""

    def __init__(self, client: TestClient, num_concurrent_users: int = 10):
        self.client = client
        self.num_concurrent_users = num_concurrent_users
        self.test_prompts: List[str] = []
        self.test_users: List[str] = []
        self.results: Dict[str, Any] = {}

    def setup_test_data(self):
        """Set up test data for performance testing."""
        # Create test prompts
        for i in range(5):
            prompt_data = {
                "name": f"perf_test_prompt_{i}_{uuid.uuid4().hex[:8]}",
                "category": "performance_testing",
                "content": f"Analyze this input {{input}} using method {i}",
                "variables": ["input"],
                "created_by": "perf_test_user"
            }

            response = self.client.post("/api/v1/prompts", json=prompt_data)
            if response.status_code == 201:
                self.test_prompts.append(response.json()["data"]["id"])

        # Create test user IDs
        self.test_users = [f"perf_user_{i}" for i in range(self.num_concurrent_users)]

    def measure_response_time(self, operation: callable, *args, **kwargs) -> float:
        """Measure the response time of an operation."""
        start_time = time.time()
        result = operation(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time, result

    def run_concurrent_requests(self, operation: callable, num_requests: int) -> List[float]:
        """Run multiple requests concurrently and measure response times."""
        response_times = []

        async def run_single_request(i: int):
            response_time, _ = self.measure_response_time(operation, i)
            response_times.append(response_time)

        async def run_all_requests():
            tasks = [run_single_request(i) for i in range(num_requests)]
            await asyncio.gather(*tasks)

        asyncio.run(run_all_requests())
        return response_times

    def test_prompt_creation_performance(self):
        """Test performance of prompt creation."""
        def create_prompt(i: int):
            prompt_data = {
                "name": f"perf_create_{i}_{uuid.uuid4().hex[:8]}",
                "category": "performance_test",
                "content": f"Test prompt {i}: {{input}}",
                "variables": ["input"],
                "created_by": f"user_{i}"
            }
            return self.client.post("/api/v1/prompts", json=prompt_data)

        print("Testing prompt creation performance...")
        response_times = self.run_concurrent_requests(create_prompt, 50)

        self.results["prompt_creation"] = {
            "total_requests": len(response_times),
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18],  # 95th percentile
            "requests_per_second": len(response_times) / sum(response_times)
        }

    def test_analytics_recording_performance(self):
        """Test performance of analytics recording."""
        if not self.test_prompts:
            return

        def record_analytics(i: int):
            prompt_id = self.test_prompts[i % len(self.test_prompts)]
            usage_data = {
                "success": True,
                "response_time_ms": 800 + (i % 400),  # Vary between 800-1200ms
                "input_tokens": 50 + (i % 50),
                "output_tokens": 100 + (i % 100),
                "llm_service": "gpt-4" if i % 2 == 0 else "gpt-3.5-turbo"
            }
            return self.client.post(
                f"/api/v1/analytics/usage?prompt_id={prompt_id}&version=1",
                json=usage_data
            )

        print("Testing analytics recording performance...")
        response_times = self.run_concurrent_requests(record_analytics, 100)

        self.results["analytics_recording"] = {
            "total_requests": len(response_times),
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18],
            "requests_per_second": len(response_times) / sum(response_times)
        }

    def test_ab_testing_operations_performance(self):
        """Test performance of A/B testing operations."""
        if len(self.test_prompts) < 2:
            return

        # Create an A/B test
        test_response = self.client.post(
            "/api/v1/optimization/ab-tests",
            params={
                "prompt_a_id": self.test_prompts[0],
                "prompt_b_id": self.test_prompts[1],
                "traffic_percentage": 50.0
            }
        )

        if test_response.status_code != 200:
            return

        test_id = test_response.json()["data"]["test_id"]

        def get_assignment(i: int):
            user_id = self.test_users[i % len(self.test_users)]
            return self.client.get(
                f"/api/v1/optimization/ab-tests/{test_id}/assign",
                params={"user_id": user_id}
            )

        print("Testing A/B testing assignment performance...")
        response_times = self.run_concurrent_requests(get_assignment, 200)

        self.results["ab_testing_assignments"] = {
            "total_requests": len(response_times),
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18],
            "requests_per_second": len(response_times) / sum(response_times)
        }

    def test_validation_operations_performance(self):
        """Test performance of validation operations."""
        test_prompts = [
            "Analyze this code: {code}",
            "Review the following documentation: {docs}",
            "Generate a summary of: {content}",
            "Identify issues in: {text}",
            "Provide feedback on: {submission}"
        ]

        def lint_prompt(i: int):
            prompt_content = test_prompts[i % len(test_prompts)]
            return self.client.post(
                "/api/v1/validation/lint",
                json={"prompt_content": prompt_content}
            )

        print("Testing prompt linting performance...")
        response_times = self.run_concurrent_requests(lint_prompt, 100)

        self.results["prompt_linting"] = {
            "total_requests": len(response_times),
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18],
            "requests_per_second": len(response_times) / sum(response_times)
        }

    def test_orchestration_operations_performance(self):
        """Test performance of orchestration operations."""
        def select_optimal_prompt(i: int):
            task_descriptions = [
                "Code review for Python",
                "Documentation generation",
                "Content analysis",
                "Bug detection",
                "Performance optimization"
            ]
            task = task_descriptions[i % len(task_descriptions)]
            return self.client.post(
                "/api/v1/orchestration/prompts/select",
                json={"task_description": task}
            )

        print("Testing prompt selection performance...")
        response_times = self.run_concurrent_requests(select_optimal_prompt, 50)

        self.results["prompt_selection"] = {
            "total_requests": len(response_times),
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18],
            "requests_per_second": len(response_times) / sum(response_times)
        }

    def test_dashboard_queries_performance(self):
        """Test performance of dashboard and analytics queries."""
        def get_dashboard(i: int):
            time_ranges = [1, 7, 30, 90]
            days = time_ranges[i % len(time_ranges)]
            return self.client.get(f"/api/v1/analytics/dashboard?time_range_days={days}")

        print("Testing dashboard query performance...")
        response_times = self.run_concurrent_requests(get_dashboard, 20)

        self.results["dashboard_queries"] = {
            "total_requests": len(response_times),
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18],
            "requests_per_second": len(response_times) / sum(response_times)
        }

    def run_all_performance_tests(self):
        """Run all performance tests and generate report."""
        print("🚀 Starting Advanced Prompt Ecosystem Performance Tests")
        print("=" * 60)

        self.setup_test_data()

        # Run individual tests
        self.test_prompt_creation_performance()
        self.test_analytics_recording_performance()
        self.test_ab_testing_operations_performance()
        self.test_validation_operations_performance()
        self.test_orchestration_operations_performance()
        self.test_dashboard_queries_performance()

        # Generate performance report
        self.generate_performance_report()

    def generate_performance_report(self):
        """Generate a comprehensive performance report."""
        print("\n📊 PERFORMANCE TEST RESULTS")
        print("=" * 60)

        for test_name, metrics in self.results.items():
            print(f"\n🔍 {test_name.replace('_', ' ').title()}")
            print("-" * 40)
            print(f"  Total Requests: {metrics['total_requests']}")
            print(".3f")
            print(".3f")
            print(".3f")
            print(".3f")
            print(".3f")
            print(".2f")

        # Overall assessment
        print("\n🎯 PERFORMANCE ASSESSMENT")
        print("-" * 40)

        all_response_times = []
        for metrics in self.results.values():
            # Collect response time samples (approximated)
            avg_time = metrics['avg_response_time']
            all_response_times.extend([avg_time] * metrics['total_requests'])

        if all_response_times:
            overall_avg = statistics.mean(all_response_times)
            overall_p95 = statistics.quantiles(all_response_times, n=20)[18] if len(all_response_times) >= 20 else max(all_response_times)

            print(".3f")
            print(".3f")

            # Performance rating
            if overall_p95 < 0.5:
                rating = "🟢 EXCELLENT"
            elif overall_p95 < 1.0:
                rating = "🟡 GOOD"
            elif overall_p95 < 2.0:
                rating = "🟠 ACCEPTABLE"
            else:
                rating = "🔴 NEEDS OPTIMIZATION"

            print(f"Performance Rating: {rating}")

        print("\n✅ Performance testing completed!")


@pytest.mark.performance
class TestAdvancedEcosystemPerformance:
    """Performance tests for the advanced prompt ecosystem."""

    def test_full_ecosystem_performance(self, test_client):
        """Run comprehensive performance tests on the advanced ecosystem."""
        suite = PerformanceTestSuite(test_client, num_concurrent_users=5)
        suite.run_all_performance_tests()

        # Verify that we have results
        assert len(suite.results) > 0

        # Verify key metrics are present
        expected_tests = [
            "prompt_creation", "analytics_recording", "ab_testing_assignments",
            "prompt_linting", "prompt_selection", "dashboard_queries"
        ]

        for test_name in expected_tests:
            assert test_name in suite.results
            metrics = suite.results[test_name]
            assert "avg_response_time" in metrics
            assert "p95_response_time" in metrics
            assert "requests_per_second" in metrics

    def test_concurrent_analytics_load(self, test_client):
        """Test analytics system under concurrent load."""
        suite = PerformanceTestSuite(test_client, num_concurrent_users=10)

        # Create test prompt
        prompt_data = {
            "name": f"load_test_{uuid.uuid4().hex[:8]}",
            "category": "load_testing",
            "content": "Process this: {input}",
            "variables": ["input"],
            "created_by": "load_test_user"
        }

        response = test_client.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201
        prompt_id = response.json()["data"]["id"]

        # Simulate concurrent analytics recording
        def record_usage(i: int):
            usage_data = {
                "success": i % 10 != 0,  # 90% success rate
                "response_time_ms": 500 + (i % 1000),
                "input_tokens": 25 + (i % 50),
                "output_tokens": 75 + (i % 100),
                "llm_service": "gpt-4"
            }
            return test_client.post(
                f"/api/v1/analytics/usage?prompt_id={prompt_id}&version=1",
                json=usage_data
            )

        print("Testing concurrent analytics load...")
        response_times = suite.run_concurrent_requests(record_usage, 50)

        # Analyze results
        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]
        rps = len(response_times) / sum(response_times)

        print(".3f")
        print(".3f")
        print(".2f")

        # Assert reasonable performance under load
        assert avg_time < 2.0  # Should handle load within 2 seconds average
        assert p95_time < 5.0  # P95 should be under 5 seconds
        assert rps > 5.0       # Should handle at least 5 requests per second

    def test_validation_pipeline_performance(self, test_client):
        """Test the validation pipeline performance."""
        suite = PerformanceTestSuite(test_client, num_concurrent_users=5)

        complex_prompts = [
            """Analyze the following code for potential security vulnerabilities,
            performance issues, and code quality problems. Provide detailed
            explanations for each issue found and suggest specific improvements.
            Consider the following aspects: input validation, error handling,
            resource management, concurrency safety, and adherence to best practices.

            Code to analyze: {code}

            Also provide an overall quality score from 1-10 and justify your rating.""",

            """You are a senior software architect reviewing a system design document.
            Evaluate the proposed architecture for scalability, maintainability,
            security, and performance. Identify potential bottlenecks, single points
            of failure, and areas for improvement. Suggest alternative approaches
            where appropriate and provide specific recommendations.

            Document to review: {document}

            Rate the architecture quality from 1-10 and explain your assessment.""",

            """Review this pull request description and code changes. Assess whether
            the changes adequately address the requirements, follow coding standards,
            include appropriate tests, and maintain backward compatibility. Identify
            any potential issues, security concerns, or performance implications.

            PR Description: {pr_description}
            Code Changes: {code_changes}

            Provide a recommendation to merge, request changes, or reject.""",
        ]

        def validate_complex_prompt(i: int):
            prompt_content = complex_prompts[i % len(complex_prompts)]

            # Run multiple validation operations
            operations = []

            # Lint the prompt
            lint_start = time.time()
            lint_response = test_client.post(
                "/api/v1/validation/lint",
                json={"prompt_content": prompt_content}
            )
            lint_time = time.time() - lint_start
            operations.append(("lint", lint_time, lint_response.status_code))

            # Detect bias
            bias_start = time.time()
            bias_response = test_client.post(
                "/api/v1/validation/bias-detect",
                json={"prompt_content": prompt_content}
            )
            bias_time = time.time() - bias_start
            operations.append(("bias", bias_time, bias_response.status_code))

            # Validate sample output
            sample_output = "This is a comprehensive analysis with proper structure and detailed recommendations."
            validate_start = time.time()
            validate_response = test_client.post(
                "/api/v1/validation/output",
                json={
                    "prompt_output": sample_output,
                    "expected_criteria": {
                        "min_length": 50,
                        "requires_structure": True
                    }
                }
            )
            validate_time = time.time() - validate_start
            operations.append(("validate", validate_time, validate_response.status_code))

            total_time = lint_time + bias_time + validate_time
            return total_time, operations

        print("Testing validation pipeline performance...")
        response_times = suite.run_concurrent_requests(validate_complex_prompt, 20)

        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]

        print(".3f")
        print(".3f")

        # Validation pipeline should be reasonably fast
        assert avg_time < 3.0  # Should complete within 3 seconds on average
        assert p95_time < 5.0  # P95 should be under 5 seconds
