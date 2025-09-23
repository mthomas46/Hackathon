"""
Test Helpers and Utilities

Comprehensive testing utilities for the Unified API Dashboard including:
- Test data generation
- Mock factories
- Assertion helpers
- Performance testing utilities
- Security testing helpers
"""

import asyncio
import hashlib
import hmac
import json
import random
import string
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

import pytest
from httpx import AsyncClient

# ============================================================================
# TEST DATA GENERATION
# ============================================================================


class TestDataGenerator:
    """Generate realistic test data for various scenarios."""

    @staticmethod
    def generate_openapi_spec(service_name: str = "test-service", version: str = "1.0.0") -> Dict[str, Any]:
        """Generate a realistic OpenAPI specification."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": f"{service_name.replace('-', ' ').title()} API",
                "version": version,
                "description": f"API for {service_name}",
                "contact": {"name": "API Team", "email": "api@unified-api.local"},
            },
            "servers": [
                {"url": f"http://localhost:8000/{service_name}"},
                {"url": f"https://api.example.com/{service_name}"},
            ],
            "security": [{"bearerAuth": []}],
            "paths": {
                "/health": {
                    "get": {
                        "summary": "Health check",
                        "description": "Check service health status",
                        "responses": {
                            "200": {
                                "description": "Service is healthy",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                                                "timestamp": {"type": "string", "format": "date-time"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
                "/users": {
                    "get": {
                        "summary": "List users",
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10},
                            },
                            {
                                "name": "offset",
                                "in": "query",
                                "schema": {"type": "integer", "minimum": 0, "default": 0},
                            },
                        ],
                        "responses": {
                            "200": {
                                "description": "List of users",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "users": {
                                                    "type": "array",
                                                    "items": {"$ref": "#/components/schemas/User"},
                                                },
                                                "total": {"type": "integer"},
                                                "limit": {"type": "integer"},
                                                "offset": {"type": "integer"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    },
                    "post": {
                        "summary": "Create user",
                        "requestBody": {
                            "required": True,
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserInput"}}},
                        },
                        "responses": {
                            "201": {
                                "description": "User created",
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}},
                            }
                        },
                    },
                },
                "/users/{userId}": {
                    "get": {
                        "summary": "Get user by ID",
                        "parameters": [
                            {"name": "userId", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {
                            "200": {
                                "description": "User details",
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}},
                            },
                            "404": {"description": "User not found"},
                        },
                    },
                    "put": {
                        "summary": "Update user",
                        "parameters": [
                            {"name": "userId", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserUpdate"}}},
                        },
                        "responses": {
                            "200": {
                                "description": "User updated",
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}},
                            }
                        },
                    },
                    "delete": {
                        "summary": "Delete user",
                        "parameters": [
                            {"name": "userId", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {"204": {"description": "User deleted"}, "404": {"description": "User not found"}},
                    },
                },
            },
            "components": {
                "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "username": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "created_at": {"type": "string", "format": "date-time"},
                            "updated_at": {"type": "string", "format": "date-time"},
                        },
                    },
                    "UserInput": {
                        "type": "object",
                        "required": ["username", "email"],
                        "properties": {
                            "username": {"type": "string", "minLength": 3, "maxLength": 50},
                            "email": {"type": "string", "format": "email"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                        },
                    },
                    "UserUpdate": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "format": "email"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                        },
                    },
                },
            },
        }

    @staticmethod
    def generate_api_request(service: str = "test-service", endpoint: str = "/users") -> Dict[str, Any]:
        """Generate a sample API request."""
        return {
            "service_name": service,
            "endpoint_path": endpoint,
            "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "headers": {
                "Authorization": f"Bearer {TestDataGenerator.generate_jwt_token()}",
                "Content-Type": "application/json",
                "User-Agent": "TestClient/1.0",
            },
            "params": {"limit": random.randint(1, 100), "offset": random.randint(0, 1000)},
            "body": TestDataGenerator.generate_random_json() if random.random() > 0.5 else None,
        }

    @staticmethod
    def generate_usage_data(count: int = 100) -> List[Dict[str, Any]]:
        """Generate realistic API usage data."""
        services = ["user-service", "auth-service", "data-service", "api-gateway"]
        endpoints = ["/users", "/auth/login", "/data", "/health", "/metrics"]
        methods = ["GET", "POST", "PUT", "DELETE"]
        status_codes = [200, 201, 400, 401, 403, 404, 500]

        usage_data = []
        base_time = datetime.now() - timedelta(days=7)

        for i in range(count):
            usage_data.append(
                {
                    "timestamp": base_time + timedelta(minutes=i * 10),
                    "service": random.choice(services),
                    "endpoint": random.choice(endpoints),
                    "method": random.choice(methods),
                    "response_time": random.randint(50, 2000),  # ms
                    "status_code": random.choice(status_codes),
                    "user_id": f"user_{random.randint(1, 100)}",
                    "ip_address": f"192.168.1.{random.randint(1, 255)}",
                    "user_agent": random.choice(
                        [
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                            "PostmanRuntime/7.29.0",
                            "curl/7.68.0",
                        ]
                    ),
                }
            )

        return usage_data

    @staticmethod
    def generate_error_data(count: int = 50) -> List[Dict[str, Any]]:
        """Generate realistic API error data."""
        services = ["user-service", "auth-service", "data-service"]
        error_types = [
            "validation_error",
            "authentication_error",
            "authorization_error",
            "not_found",
            "server_error",
            "timeout",
        ]
        endpoints = ["/users", "/auth/login", "/data", "/profile"]

        error_data = []
        base_time = datetime.now() - timedelta(days=3)

        for i in range(count):
            error_data.append(
                {
                    "timestamp": base_time + timedelta(hours=i),
                    "service": random.choice(services),
                    "endpoint": random.choice(endpoints),
                    "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                    "error_type": random.choice(error_types),
                    "error_message": f"Error {i}: {random.choice(error_types).replace('_', ' ')}",
                    "status_code": random.choice([400, 401, 403, 404, 422, 500, 502, 503]),
                    "user_id": f"user_{random.randint(1, 50)}" if random.random() > 0.3 else None,
                    "stack_trace": f"Traceback (most recent call last):\n  File \"app.py\", line {random.randint(10, 200)}, in handler\n    {random.choice(['ValueError', 'KeyError', 'TypeError'])}: {random.choice(['Invalid input', 'Key not found', 'Type mismatch'])}",
                    "request_id": str(uuid.uuid4()),
                }
            )

        return error_data

    @staticmethod
    def generate_service_topology() -> Dict[str, Any]:
        """Generate a realistic service topology."""
        return {
            "services": ["api-gateway", "user-service", "auth-service", "data-service", "notification-service"],
            "relationships": [
                {"from": "api-gateway", "to": "user-service", "calls": 1250, "avg_response_time": 120},
                {"from": "api-gateway", "to": "auth-service", "calls": 980, "avg_response_time": 80},
                {"from": "api-gateway", "to": "data-service", "calls": 750, "avg_response_time": 200},
                {"from": "user-service", "to": "data-service", "calls": 680, "avg_response_time": 150},
                {"from": "user-service", "to": "notification-service", "calls": 120, "avg_response_time": 90},
                {"from": "auth-service", "to": "data-service", "calls": 340, "avg_response_time": 110},
            ],
            "health_status": {
                "api-gateway": "healthy",
                "user-service": "healthy",
                "auth-service": "degraded",
                "data-service": "healthy",
                "notification-service": "healthy",
            },
            "dependencies": {
                "api-gateway": ["user-service", "auth-service", "data-service"],
                "user-service": ["data-service", "notification-service"],
                "auth-service": ["data-service"],
                "data-service": [],
                "notification-service": [],
            },
        }

    @staticmethod
    def generate_jwt_token(user_id: str = "test_user", role: str = "developer") -> str:
        """Generate a mock JWT token."""
        import jwt

        payload = {
            "user_id": user_id,
            "username": f"user_{user_id}",
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
        }

        # Use a test secret (in real scenarios, use proper secret management)
        secret = "test_jwt_secret_for_testing_only"
        return jwt.encode(payload, secret, algorithm="HS256")

    @staticmethod
    def generate_random_json(depth: int = 2) -> Dict[str, Any]:
        """Generate random JSON data for testing."""
        if depth <= 0:
            return TestDataGenerator.generate_random_value()

        data = {}
        num_fields = random.randint(1, 5)

        for _ in range(num_fields):
            key = "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 10)))
            data[key] = TestDataGenerator.generate_random_value()

        return data

    @staticmethod
    def generate_random_value() -> Any:
        """Generate a random value of various types."""
        value_types = [str, int, float, bool, list]

        value_type = random.choice(value_types)

        if value_type == str:
            return "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 20)))
        elif value_type == int:
            return random.randint(1, 1000)
        elif value_type == float:
            return round(random.uniform(0, 100), 2)
        elif value_type == bool:
            return random.choice([True, False])
        elif value_type == list:
            return [TestDataGenerator.generate_random_value() for _ in range(random.randint(1, 5))]


# ============================================================================
# PERFORMANCE TESTING UTILITIES
# ============================================================================


@dataclass
class PerformanceTestResult:
    """Results from a performance test."""

    test_name: str
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceTester:
    """Utilities for performance testing."""

    @staticmethod
    async def run_load_test(
        client: AsyncClient,
        endpoint: str,
        method: str = "GET",
        num_requests: int = 100,
        concurrent_users: int = 10,
        timeout: float = 30.0,
    ) -> PerformanceTestResult:
        """Run a load test against an endpoint."""
        start_time = time.time()
        response_times = []
        success_count = 0
        error_count = 0

        async def make_request():
            nonlocal success_count, error_count
            req_start = time.time()

            try:
                response = await client.request(method, endpoint, timeout=timeout)
                req_end = time.time()
                response_times.append(req_end - req_start)

                if response.status_code < 400:
                    success_count += 1
                else:
                    error_count += 1

            except Exception:
                req_end = time.time()
                response_times.append(req_end - req_start)
                error_count += 1

        # Run requests with concurrency control
        semaphore = asyncio.Semaphore(concurrent_users)

        async def limited_request():
            async with semaphore:
                await make_request()

        tasks = [limited_request() for _ in range(num_requests)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # Calculate statistics
        if response_times:
            sorted_times = sorted(response_times)
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p50 = sorted_times[int(len(sorted_times) * 0.5)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            rps = len(response_times) / duration if duration > 0 else 0
            error_rate = error_count / len(response_times)
        else:
            avg_time = min_time = max_time = p50 = p95 = p99 = rps = error_rate = 0

        return PerformanceTestResult(
            test_name=f"load_test_{endpoint}",
            duration_seconds=duration,
            total_requests=num_requests,
            successful_requests=success_count,
            failed_requests=error_count,
            avg_response_time=avg_time * 1000,  # Convert to ms
            min_response_time=min_time * 1000,
            max_response_time=max_time * 1000,
            p50_response_time=p50 * 1000,
            p95_response_time=p95 * 1000,
            p99_response_time=p99 * 1000,
            requests_per_second=rps,
            error_rate=error_rate,
        )

    @staticmethod
    async def run_stress_test(
        client: AsyncClient, endpoint: str, duration_seconds: int = 60, max_concurrent: int = 50
    ) -> List[PerformanceTestResult]:
        """Run a stress test with increasing load."""
        results = []

        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 25, 50]

        for concurrency in concurrency_levels:
            if concurrency > max_concurrent:
                break

            print(f"Testing with {concurrency} concurrent users...")

            # Calculate number of requests for this test
            num_requests = concurrency * 10  # 10 requests per concurrent user

            result = await PerformanceTester.run_load_test(
                client=client, endpoint=endpoint, num_requests=num_requests, concurrent_users=concurrency, timeout=10.0
            )

            results.append(result)

            # Small delay between tests
            await asyncio.sleep(1)

        return results


# ============================================================================
# SECURITY TESTING HELPERS
# ============================================================================


class SecurityTestHelper:
    """Helpers for security testing."""

    @staticmethod
    def generate_sql_injection_payloads() -> List[str]:
        """Generate SQL injection test payloads."""
        return [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users; --",
            "admin' --",
            "' OR 1=1; --",
            "') OR ('1'='1",
        ]

    @staticmethod
    def generate_xss_payloads() -> List[str]:
        """Generate XSS test payloads."""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<svg onload=alert('XSS')>",
        ]

    @staticmethod
    def generate_large_payload(size_mb: int = 10) -> str:
        """Generate a large payload for testing."""
        # Generate approximately size_mb megabytes of data
        chars_per_mb = 1024 * 1024
        return "x" * (size_mb * chars_per_mb)

    @staticmethod
    def generate_malformed_json() -> List[str]:
        """Generate malformed JSON payloads."""
        return [
            '{"incomplete": "json"',
            '{"missing": "comma" "invalid": "json"}',
            '{"nested": {"incomplete": "object"}',
            '["unclosed", "array"',
            '{"duplicate": "key", "duplicate": "value"}',
            '{"null": null, "undefined": undefined}',
        ]

    @staticmethod
    async def test_authentication_bypass(client: AsyncClient, endpoints: List[str]) -> Dict[str, Any]:
        """Test for authentication bypass vulnerabilities."""
        results = {}

        for endpoint in endpoints:
            # Test without authentication
            response = await client.get(endpoint)
            if response.status_code not in [401, 403]:
                results[endpoint] = {
                    "vulnerable": True,
                    "status_code": response.status_code,
                    "reason": "Endpoint accessible without authentication",
                }

            # Test with invalid token
            headers = {"Authorization": "Bearer invalid_token"}
            response = await client.get(endpoint, headers=headers)
            if response.status_code not in [401, 403]:
                results[endpoint] = {
                    "vulnerable": True,
                    "status_code": response.status_code,
                    "reason": "Endpoint accessible with invalid token",
                }

        return results

    @staticmethod
    async def test_rate_limiting(client: AsyncClient, endpoint: str, num_requests: int = 100) -> Dict[str, Any]:
        """Test rate limiting effectiveness."""
        success_count = 0
        rate_limited_count = 0

        for _ in range(num_requests):
            response = await client.get(endpoint)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1

        return {
            "total_requests": num_requests,
            "successful_requests": success_count,
            "rate_limited_requests": rate_limited_count,
            "rate_limiting_effective": rate_limited_count > 0,
        }


# ============================================================================
# ASSERTION HELPERS
# ============================================================================


class AssertionHelpers:
    """Custom assertion helpers for testing."""

    @staticmethod
    def assert_valid_openapi_spec(spec: Dict[str, Any]):
        """Assert that a dictionary is a valid OpenAPI specification."""
        assert isinstance(spec, dict), "OpenAPI spec must be a dictionary"
        assert "openapi" in spec, "OpenAPI spec must have 'openapi' field"
        assert "info" in spec, "OpenAPI spec must have 'info' field"
        assert "paths" in spec, "OpenAPI spec must have 'paths' field"

        # Check version format
        assert spec["openapi"].startswith("3."), "Must be OpenAPI 3.x"

        # Check info structure
        info = spec["info"]
        assert "title" in info, "Info must have title"
        assert "version" in info, "Info must have version"

    @staticmethod
    def assert_valid_api_response(response: Dict[str, Any]):
        """Assert that an API response follows the standard format."""
        assert isinstance(response, dict), "Response must be a dictionary"
        assert "success" in response, "Response must have 'success' field"
        assert isinstance(response["success"], bool), "Success must be boolean"
        assert "timestamp" in response, "Response must have timestamp"

        if response["success"]:
            assert "data" in response, "Successful response must have 'data' field"
        else:
            assert "message" in response, "Failed response must have 'message' field"

    @staticmethod
    def assert_performance_thresholds(result: PerformanceTestResult, thresholds: Dict[str, Any]):
        """Assert that performance results meet thresholds."""
        if "max_response_time" in thresholds:
            assert (
                result.avg_response_time <= thresholds["max_response_time"]
            ), f"Average response time {result.avg_response_time}ms exceeds threshold {thresholds['max_response_time']}ms"

        if "max_error_rate" in thresholds:
            assert (
                result.error_rate <= thresholds["max_error_rate"]
            ), f"Error rate {result.error_rate:.2%} exceeds threshold {thresholds['max_error_rate']:.2%}"

        if "min_requests_per_second" in thresholds:
            assert (
                result.requests_per_second >= thresholds["min_requests_per_second"]
            ), f"RPS {result.requests_per_second} below threshold {thresholds['min_requests_per_second']}"

    @staticmethod
    def assert_security_compliance(security_events: List[Dict[str, Any]], max_critical: int = 0):
        """Assert that security events meet compliance requirements."""
        critical_events = [e for e in security_events if e.get("threat_level") == "critical"]
        assert (
            len(critical_events) <= max_critical
        ), f"Found {len(critical_events)} critical security events, max allowed: {max_critical}"

    @staticmethod
    def assert_coverage_meets_threshold(coverage_data: Dict[str, Any], min_coverage: float = 80.0):
        """Assert that test coverage meets minimum threshold."""
        if "totals" in coverage_data:
            total_coverage = coverage_data["totals"]["percent_covered"]
            assert (
                total_coverage >= min_coverage
            ), f"Coverage {total_coverage:.1f}% below minimum threshold {min_coverage:.1f}%"


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def test_data_generator():
    """Fixture providing test data generator."""
    return TestDataGenerator()


@pytest.fixture
def performance_tester():
    """Fixture providing performance testing utilities."""
    return PerformanceTester()


@pytest.fixture
def security_test_helper():
    """Fixture providing security testing helpers."""
    return SecurityTestHelper()


@pytest.fixture
def assertion_helpers():
    """Fixture providing custom assertion helpers."""
    return AssertionHelpers()
