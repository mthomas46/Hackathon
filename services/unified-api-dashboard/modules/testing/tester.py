"""
API Tester

Provides interactive API testing capabilities for the Unified API Dashboard including:
- Request builder and execution
- Authentication handling
- Response validation and formatting
- Test history and analytics
- Performance benchmarking
- Automated test scenarios
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

import httpx

from ...modules.discovery.client import DiscoveryClient
from ...modules.api.catalog import APICatalogManager
from ...config import Config


class APITestRequest:
    """Represents an API test request."""

    def __init__(self, service_name: str, method: str, path: str, **kwargs):
        self.service_name = service_name
        self.method = method.upper()
        self.path = path
        self.headers = kwargs.get("headers", {})
        self.params = kwargs.get("params", {})
        self.body = kwargs.get("body")
        self.auth_token = kwargs.get("auth_token")
        self.timeout = kwargs.get("timeout", 30)
        self.expected_status = kwargs.get("expected_status", 200)
        self.expected_response_time = kwargs.get("expected_response_time", 5000)  # 5 seconds
        self.validate_response = kwargs.get("validate_response", True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "service_name": self.service_name,
            "method": self.method,
            "path": self.path,
            "headers": self.headers,
            "params": self.params,
            "body": self.body,
            "auth_token": self.auth_token,
            "timeout": self.timeout,
            "expected_status": self.expected_status,
            "expected_response_time": self.expected_response_time,
            "validate_response": self.validate_response
        }


class APITestResult:
    """Result of an API test execution."""

    def __init__(self, request: APITestRequest, response_time: float,
                 status_code: int, response_headers: Dict[str, str],
                 response_body: Any, error_message: Optional[str] = None):
        self.request = request
        self.response_time = response_time
        self.status_code = status_code
        self.response_headers = response_headers
        self.response_body = response_body
        self.error_message = error_message
        self.timestamp = datetime.now()
        self.success = error_message is None and status_code == request.expected_status

        # Performance validation
        self.performance_ok = response_time <= request.expected_response_time

        # Response validation
        self.validation_errors = []
        if request.validate_response and error_message is None:
            self.validation_errors = self._validate_response()

    def _validate_response(self) -> List[str]:
        """Validate the response against expectations."""
        errors = []

        # Basic JSON validation for JSON responses
        if self.response_headers.get("content-type", "").startswith("application/json"):
            try:
                if isinstance(self.response_body, str):
                    json.loads(self.response_body)
            except json.JSONDecodeError:
                errors.append("Invalid JSON response")

        # Status code validation
        if self.status_code != self.request.expected_status:
            errors.append(f"Expected status {self.request.expected_status}, got {self.status_code}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "request": self.request.to_dict(),
            "response_time": self.response_time,
            "status_code": self.status_code,
            "response_headers": self.response_headers,
            "response_body": self.response_body,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "performance_ok": self.performance_ok,
            "validation_errors": self.validation_errors
        }


class APITester:
    """Provides API testing capabilities for the Unified API Dashboard."""

    def __init__(self, discovery_client: DiscoveryClient, catalog_manager: APICatalogManager, config: Config):
        self.discovery_client = discovery_client
        self.catalog_manager = catalog_manager
        self.config = config

        # HTTP client for API testing
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
        )

        # Test history storage
        self.test_history: List[APITestResult] = []
        self.max_history_size = 1000

    async def test_endpoint(self, request: APITestRequest) -> APITestResult:
        """Execute an API test request."""
        try:
            # Get service URL from discovery
            service_info = await self.discovery_client.get_service_details(request.service_name)
            if not service_info:
                return APITestResult(
                    request=request,
                    response_time=0,
                    status_code=0,
                    response_headers={},
                    response_body=None,
                    error_message=f"Service {request.service_name} not found"
                )

            service_url = service_info.get("url")
            if not service_url:
                return APITestResult(
                    request=request,
                    response_time=0,
                    status_code=0,
                    response_headers={},
                    response_body=None,
                    error_message=f"No URL available for service {request.service_name}"
                )

            # Construct full URL
            url = f"{service_url.rstrip('/')}{request.path}"

            # Prepare headers
            headers = request.headers.copy()
            if request.auth_token:
                headers["Authorization"] = f"Bearer {request.auth_token}"

            # Set content type for JSON body
            if request.body and isinstance(request.body, (dict, list)):
                headers["Content-Type"] = "application/json"
                request_body = json.dumps(request.body)
            else:
                request_body = request.body

            # Execute request
            start_time = time.time()

            response = await self.client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.params,
                content=request_body,
                timeout=request.timeout
            )

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds

            # Parse response
            try:
                if response.headers.get("content-type", "").startswith("application/json"):
                    response_body = response.json()
                else:
                    response_body = response.text
            except:
                response_body = response.text

            # Create test result
            result = APITestResult(
                request=request,
                response_time=response_time,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                response_body=response_body
            )

        except httpx.TimeoutException:
            result = APITestResult(
                request=request,
                response_time=request.timeout * 1000,
                status_code=0,
                response_headers={},
                response_body=None,
                error_message=f"Request timeout after {request.timeout}s"
            )

        except httpx.ConnectError:
            result = APITestResult(
                request=request,
                response_time=0,
                status_code=0,
                response_headers={},
                response_body=None,
                error_message="Connection failed"
            )

        except Exception as e:
            result = APITestResult(
                request=request,
                response_time=0,
                status_code=0,
                response_headers={},
                response_body=None,
                error_message=str(e)
            )

        # Store in history
        self._add_to_history(result)

        return result

    def _add_to_history(self, result: APITestResult):
        """Add test result to history."""
        self.test_history.append(result)

        # Maintain max history size
        if len(self.test_history) > self.max_history_size:
            self.test_history = self.test_history[-self.max_history_size:]

    async def test_from_catalog(self, service_name: str, endpoint_path: str, method: str = "GET",
                               **kwargs) -> Optional[APITestResult]:
        """Test an endpoint from the API catalog."""
        # Get endpoint details from catalog
        catalog_entry = None
        if service_name in self.catalog_manager.catalog:
            for entry in self.catalog_manager.catalog[service_name]:
                if entry.path == endpoint_path and entry.method == method.upper():
                    catalog_entry = entry
                    break

        if not catalog_entry:
            # Create basic request if not in catalog
            request = APITestRequest(service_name, method, endpoint_path, **kwargs)
        else:
            # Use catalog information to build request
            request = APITestRequest(
                service_name=service_name,
                method=method,
                path=endpoint_path,
                headers=kwargs.get("headers", {}),
                params=kwargs.get("params", {}),
                body=kwargs.get("body"),
                auth_token=kwargs.get("auth_token"),
                timeout=kwargs.get("timeout", 30),
                expected_status=kwargs.get("expected_status", 200)
            )

        return await self.test_endpoint(request)

    async def run_performance_test(self, request: APITestRequest, iterations: int = 10,
                                  concurrent: bool = False) -> Dict[str, Any]:
        """Run performance test on an endpoint."""
        results = []

        if concurrent:
            # Run tests concurrently
            tasks = [self.test_endpoint(request) for _ in range(iterations)]
            results = await asyncio.gather(*tasks)
        else:
            # Run tests sequentially
            for _ in range(iterations):
                result = await self.test_endpoint(request)
                results.append(result)

        # Calculate statistics
        response_times = [r.response_time for r in results if r.error_message is None]
        successful_requests = sum(1 for r in results if r.success)

        stats = {
            "total_requests": len(results),
            "successful_requests": successful_requests,
            "failed_requests": len(results) - successful_requests,
            "success_rate": (successful_requests / len(results)) * 100,
            "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "requests_per_second": len(results) / (sum(response_times) / 1000) if response_times else 0,
            "results": [r.to_dict() for r in results]
        }

        return stats

    async def run_scenario_test(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a multi-step API testing scenario."""
        scenario_name = scenario.get("name", "Unnamed Scenario")
        steps = scenario.get("steps", [])

        results = {
            "scenario_name": scenario_name,
            "total_steps": len(steps),
            "successful_steps": 0,
            "failed_steps": 0,
            "step_results": [],
            "overall_success": False,
            "execution_time": 0
        }

        start_time = time.time()

        # Execute steps
        for i, step in enumerate(steps):
            step_name = step.get("name", f"Step {i+1}")

            try:
                # Build request from step
                request = APITestRequest(
                    service_name=step["service"],
                    method=step["method"],
                    path=step["path"],
                    headers=step.get("headers", {}),
                    params=step.get("params", {}),
                    body=step.get("body"),
                    auth_token=step.get("auth_token"),
                    expected_status=step.get("expected_status", 200)
                )

                # Execute test
                result = await self.test_endpoint(request)

                step_result = {
                    "step_name": step_name,
                    "step_number": i + 1,
                    "success": result.success,
                    "result": result.to_dict()
                }

                results["step_results"].append(step_result)

                if result.success:
                    results["successful_steps"] += 1
                else:
                    results["failed_steps"] += 1

                    # Stop on failure if configured
                    if step.get("stop_on_failure", False):
                        break

            except Exception as e:
                results["step_results"].append({
                    "step_name": step_name,
                    "step_number": i + 1,
                    "success": False,
                    "error": str(e)
                })
                results["failed_steps"] += 1
                break

        end_time = time.time()
        results["execution_time"] = end_time - start_time
        results["overall_success"] = results["failed_steps"] == 0

        return results

    def get_test_history(self, service_name: Optional[str] = None, limit: int = 50,
                        recent_hours: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get test history with optional filtering."""
        history = self.test_history.copy()

        # Filter by service
        if service_name:
            history = [r for r in history if r.request.service_name == service_name]

        # Filter by time
        if recent_hours:
            cutoff_time = datetime.now() - timedelta(hours=recent_hours)
            history = [r for r in history if r.timestamp >= cutoff_time]

        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x.timestamp, reverse=True)

        # Limit results
        history = history[:limit]

        return [r.to_dict() for r in history]

    def get_test_analytics(self, service_name: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Get testing analytics for the specified period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        relevant_tests = [r for r in self.test_history if r.timestamp >= cutoff_time]

        # Filter by service
        if service_name:
            relevant_tests = [r for r in relevant_tests if r.request.service_name == service_name]

        if not relevant_tests:
            return {"message": "No test data available for the specified period"}

        # Calculate analytics
        total_tests = len(relevant_tests)
        successful_tests = sum(1 for r in relevant_tests if r.success)
        failed_tests = total_tests - successful_tests

        response_times = [r.response_time for r in relevant_tests if r.error_message is None]

        # Group by service
        service_stats = defaultdict(lambda: {"total": 0, "successful": 0, "failed": 0})
        method_stats = defaultdict(lambda: {"total": 0, "successful": 0, "failed": 0})

        for result in relevant_tests:
            svc = result.request.service_name
            method = result.request.method

            service_stats[svc]["total"] += 1
            method_stats[method]["total"] += 1

            if result.success:
                service_stats[svc]["successful"] += 1
                method_stats[method]["successful"] += 1
            else:
                service_stats[svc]["failed"] += 1
                method_stats[method]["failed"] += 1

        analytics = {
            "period_hours": hours,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "service_breakdown": dict(service_stats),
            "method_breakdown": dict(method_stats),
            "performance_distribution": self._calculate_performance_distribution(response_times)
        }

        return analytics

    def _calculate_performance_distribution(self, response_times: List[float]) -> Dict[str, Any]:
        """Calculate response time distribution."""
        if not response_times:
            return {"fast": 0, "medium": 0, "slow": 0}

        fast_threshold = 500  # ms
        slow_threshold = 2000  # ms

        fast = sum(1 for rt in response_times if rt <= fast_threshold)
        slow = sum(1 for rt in response_times if rt >= slow_threshold)
        medium = len(response_times) - fast - slow

        return {
            "fast": fast,  # <= 500ms
            "medium": medium,  # 500ms - 2000ms
            "slow": slow,  # >= 2000ms
            "fast_percentage": (fast / len(response_times)) * 100,
            "medium_percentage": (medium / len(response_times)) * 100,
            "slow_percentage": (slow / len(response_times)) * 100
        }

    def create_test_scenario_template(self, service_name: str) -> Dict[str, Any]:
        """Create a test scenario template for a service."""
        endpoints = self.catalog_manager.catalog.get(service_name, [])

        # Group endpoints by functionality
        health_endpoints = [e for e in endpoints if "/health" in e.path]
        data_endpoints = [e for e in endpoints if any(word in e.path.lower() for word in ["data", "list", "get"])]
        action_endpoints = [e for e in endpoints if e.method in ["POST", "PUT", "DELETE"]]

        scenario = {
            "name": f"{service_name} Integration Test",
            "description": f"Comprehensive test scenario for {service_name}",
            "steps": []
        }

        # Add health check
        if health_endpoints:
            scenario["steps"].append({
                "name": "Health Check",
                "service": service_name,
                "method": "GET",
                "path": health_endpoints[0].path,
                "expected_status": 200,
                "stop_on_failure": True
            })

        # Add data retrieval tests
        for endpoint in data_endpoints[:3]:  # Limit to first 3
            scenario["steps"].append({
                "name": f"Test {endpoint.method} {endpoint.path}",
                "service": service_name,
                "method": endpoint.method,
                "path": endpoint.path,
                "expected_status": 200
            })

        # Add action tests (with caution)
        for endpoint in action_endpoints[:2]:  # Limit to first 2
            scenario["steps"].append({
                "name": f"Test {endpoint.method} {endpoint.path} (Check Only)",
                "service": service_name,
                "method": endpoint.method,
                "path": endpoint.path,
                "expected_status": 405,  # Method not allowed for safety
                "validate_response": False
            })

        return scenario

    def export_test_results(self, format: str = "json", service_name: Optional[str] = None,
                           hours: int = 24) -> str:
        """Export test results in various formats."""
        test_data = {
            "export_time": datetime.now().isoformat(),
            "service_filter": service_name,
            "time_period_hours": hours,
            "analytics": self.get_test_analytics(service_name, hours),
            "test_history": self.get_test_history(service_name, limit=100, recent_hours=hours)
        }

        if format == "json":
            return json.dumps(test_data, indent=2, default=str)
        elif format == "csv":
            # Simple CSV export for basic data
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(["timestamp", "service", "method", "path", "success", "response_time", "status_code"])

            # Write data
            for result in test_data["test_history"]:
                req = result["request"]
                writer.writerow([
                    result["timestamp"],
                    req["service_name"],
                    req["method"],
                    req["path"],
                    result["success"],
                    result["response_time"],
                    result["status_code"]
                ])

            return output.getvalue()
        else:
            return json.dumps(test_data, default=str)
