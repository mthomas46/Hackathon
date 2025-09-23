"""
Integration Tester

Automated API integration testing utilities for comprehensive
API validation, load testing, and regression testing.
"""

import asyncio
import time
import json
import statistics
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..discovery.client import DiscoveryClient
from ..api.catalog import APICatalogManager
from ..testing.tester import APITester
from .api_validator import APIValidator, ValidationResult


class TestType(Enum):
    """Types of integration tests."""
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    LOAD = "load"
    STRESS = "stress"
    REGRESSION = "regression"
    CONTRACT = "contract"


class TestStatus(Enum):
    """Status of test execution."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class TestCase:
    """Represents a single test case."""
    name: str
    service_name: str
    endpoint: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    data: Optional[Any] = None
    expected_status: int = 200
    expected_response_schema: Optional[Dict[str, Any]] = None
    validation_rules: List[Callable] = field(default_factory=list)
    timeout: int = 30
    retries: int = 0


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_case: TestCase
    status: TestStatus
    duration: float
    response_status: Optional[int] = None
    response_data: Optional[Any] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    """Collection of test cases."""
    name: str
    description: str
    test_type: TestType
    test_cases: List[TestCase]
    setup_steps: List[Callable] = field(default_factory=list)
    teardown_steps: List[Callable] = field(default_factory=list)
    concurrency: int = 1
    timeout: int = 300


@dataclass
class TestSuiteResult:
    """Results of a test suite execution."""
    suite: TestSuite
    results: List[TestResult]
    total_duration: float
    passed_count: int
    failed_count: int
    error_count: int
    skipped_count: int
    success_rate: float
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class IntegrationTester:
    """
    Enterprise-grade API integration testing framework.

    Provides:
    - Functional API testing
    - Load and performance testing
    - Regression testing
    - Contract testing
    - Automated test generation
    """

    def __init__(
        self,
        discovery_client: DiscoveryClient,
        catalog_manager: APICatalogManager,
        api_tester: APITester,
        api_validator: APIValidator
    ):
        self.discovery_client = discovery_client
        self.catalog_manager = catalog_manager
        self.api_tester = api_tester
        self.api_validator = api_validator

        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def run_test_suite(
        self,
        suite: TestSuite,
        progress_callback: Optional[Callable] = None
    ) -> TestSuiteResult:
        """
        Execute a complete test suite.

        Args:
            suite: Test suite to execute
            progress_callback: Optional callback for progress updates

        Returns:
            TestSuiteResult with execution results
        """
        start_time = time.time()

        # Run setup steps
        for setup_step in suite.setup_steps:
            try:
                await setup_step()
            except Exception as e:
                print(f"Setup step failed: {e}")
                # Continue with tests even if setup fails

        results = []

        # Execute tests based on concurrency
        if suite.concurrency == 1:
            # Sequential execution
            for i, test_case in enumerate(suite.test_cases):
                result = await self._execute_test_case(test_case)
                results.append(result)

                if progress_callback:
                    progress_callback(i + 1, len(suite.test_cases), result)
        else:
            # Concurrent execution
            semaphore = asyncio.Semaphore(suite.concurrency)

            async def execute_with_semaphore(test_case, index):
                async with semaphore:
                    result = await self._execute_test_case(test_case)
                    if progress_callback:
                        progress_callback(index + 1, len(suite.test_cases), result)
                    return result

            tasks = [
                execute_with_semaphore(test_case, i)
                for i, test_case in enumerate(suite.test_cases)
            ]
            results = await asyncio.gather(*tasks)

        # Run teardown steps
        for teardown_step in suite.teardown_steps:
            try:
                await teardown_step()
            except Exception as e:
                print(f"Teardown step failed: {e}")

        # Calculate statistics
        total_duration = time.time() - start_time
        passed_count = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed_count = sum(1 for r in results if r.status == TestStatus.FAILED)
        error_count = sum(1 for r in results if r.status == TestStatus.ERROR)
        skipped_count = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        total_tests = len(results)
        success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0

        # Performance metrics
        durations = [r.duration for r in results if r.duration > 0]
        performance_metrics = {}
        if durations:
            performance_metrics = {
                "avg_response_time": statistics.mean(durations),
                "min_response_time": min(durations),
                "max_response_time": max(durations),
                "median_response_time": statistics.median(durations),
                "p95_response_time": statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations),
                "requests_per_second": total_tests / total_duration if total_duration > 0 else 0
            }

        return TestSuiteResult(
            suite=suite,
            results=results,
            total_duration=total_duration,
            passed_count=passed_count,
            failed_count=failed_count,
            error_count=error_count,
            skipped_count=skipped_count,
            success_rate=round(success_rate, 2),
            performance_metrics=performance_metrics
        )

    async def generate_test_suite_from_spec(
        self,
        service_name: str,
        test_type: TestType = TestType.FUNCTIONAL,
        include_edge_cases: bool = True
    ) -> TestSuite:
        """
        Auto-generate test suite from OpenAPI specification.

        Args:
            service_name: Name of the service
            test_type: Type of tests to generate
            include_edge_cases: Whether to include edge case tests

        Returns:
            Generated TestSuite
        """
        # Get service specification
        service_info = await self.catalog_manager.get_service_details(service_name)
        if not service_info or "openapi_spec" not in service_info:
            raise ValueError(f"OpenAPI specification not found for service '{service_name}'")

        spec = service_info["openapi_spec"]
        base_url = service_info.get("base_url", f"http://{service_name}:8000")

        test_cases = []

        # Generate test cases from paths
        if "paths" in spec:
            for path, methods in spec["paths"].items():
                for method, operation in methods.items():
                    if not isinstance(operation, dict):
                        continue

                    # Create basic test case
                    test_case = TestCase(
                        name=f"{method.upper()} {path}",
                        service_name=service_name,
                        endpoint=path,
                        method=method.upper(),
                        expected_status=200
                    )

                    # Add parameters
                    if "parameters" in operation:
                        for param in operation["parameters"]:
                            param_name = param.get("name")
                            param_in = param.get("in")
                            param_required = param.get("required", False)

                            if param_required and param_in == "query":
                                # Add sample value for required parameters
                                test_case.params[param_name] = self._generate_sample_value(param.get("schema", {}))

                    # Add request body for POST/PUT/PATCH
                    if method.upper() in ["POST", "PUT", "PATCH"] and "requestBody" in operation:
                        request_body = operation["requestBody"]
                        if "content" in request_body:
                            for content_type, media_type in request_body["content"].items():
                                if "schema" in media_type:
                                    schema = media_type["schema"]
                                    test_case.data = self._generate_sample_data(schema)
                                    test_case.headers["Content-Type"] = content_type
                                    break

                    # Add response validation
                    if "responses" in operation:
                        responses = operation["responses"]
                        if "200" in responses:
                            response_200 = responses["200"]
                            if "content" in response_200:
                                for content_type, media_type in response_200["content"].items():
                                    if "schema" in media_type:
                                        test_case.expected_response_schema = media_type["schema"]
                                        break

                    test_cases.append(test_case)

                    # Generate edge cases
                    if include_edge_cases and test_type == TestType.FUNCTIONAL:
                        edge_cases = self._generate_edge_cases(test_case, operation)
                        test_cases.extend(edge_cases)

        return TestSuite(
            name=f"{service_name}_{test_type.value}_tests",
            description=f"Auto-generated {test_type.value} tests for {service_name}",
            test_type=test_type,
            test_cases=test_cases
        )

    async def run_load_test(
        self,
        service_name: str,
        endpoint: str,
        method: str = "GET",
        concurrent_users: int = 10,
        duration_seconds: int = 60,
        ramp_up_seconds: int = 10
    ) -> TestSuiteResult:
        """
        Run a load test on a specific endpoint.

        Args:
            service_name: Name of the service
            endpoint: API endpoint to test
            method: HTTP method
            concurrent_users: Number of concurrent users
            duration_seconds: Test duration in seconds
            ramp_up_seconds: Ramp-up time in seconds

        Returns:
            Load test results
        """
        # Get service base URL
        service_info = await self.catalog_manager.get_service_details(service_name)
        base_url = service_info.get("base_url", f"http://{service_name}:8000") if service_info else f"http://{service_name}:8000"

        # Create load test suite
        test_cases = []
        total_requests = concurrent_users * (duration_seconds // 2)  # Rough estimate

        for i in range(total_requests):
            test_case = TestCase(
                name=f"load_test_request_{i}",
                service_name=service_name,
                endpoint=endpoint,
                method=method,
                headers={"User-Agent": f"LoadTest-{i}"}
            )
            test_cases.append(test_case)

        suite = TestSuite(
            name=f"{service_name}_load_test",
            description=f"Load test for {method} {endpoint}",
            test_type=TestType.LOAD,
            test_cases=test_cases,
            concurrency=min(concurrent_users, 50)  # Cap concurrency
        )

        # Add ramp-up logic to setup
        async def ramp_up():
            print(f"Starting load test ramp-up for {ramp_up_seconds} seconds...")
            await asyncio.sleep(ramp_up_seconds)

        suite.setup_steps.append(ramp_up)

        return await self.run_test_suite(suite)

    async def run_contract_test(
        self,
        consumer_service: str,
        provider_service: str
    ) -> TestSuiteResult:
        """
        Run contract tests between consumer and provider services.

        Args:
            consumer_service: Name of the consuming service
            provider_service: Name of the providing service

        Returns:
            Contract test results
        """
        # Get consumer's expected API contracts
        consumer_spec = await self._get_service_spec(consumer_service)
        provider_spec = await self._get_service_spec(provider_service)

        if not provider_spec:
            raise ValueError(f"Provider service '{provider_service}' specification not found")

        test_cases = []

        # Generate contract tests based on consumer expectations vs provider capabilities
        if consumer_spec and "paths" in consumer_spec:
            for path, methods in consumer_spec["paths"].items():
                for method, operation in methods.items():
                    # Check if provider supports this endpoint
                    if path in provider_spec.get("paths", {}) and method in provider_spec["paths"][path]:
                        test_case = TestCase(
                            name=f"contract_{method}_{path}",
                            service_name=provider_service,
                            endpoint=path,
                            method=method.upper(),
                            expected_status=200
                        )

                        # Add contract validation
                        consumer_operation = operation
                        provider_operation = provider_spec["paths"][path][method]

                        async def validate_contract(response_data, response_status):
                            errors = []

                            # Validate response schema contract
                            if "responses" in consumer_operation and "responses" in provider_operation:
                                consumer_response = consumer_operation["responses"].get("200", {})
                                provider_response = provider_operation["responses"].get("200", {})

                                # Check if provider response satisfies consumer expectations
                                if not self._response_satisfies_contract(provider_response, consumer_response):
                                    errors.append("Provider response does not satisfy consumer contract")

                            return errors

                        test_case.validation_rules.append(validate_contract)
                        test_cases.append(test_case)

        suite = TestSuite(
            name=f"contract_{consumer_service}_{provider_service}",
            description=f"Contract tests between {consumer_service} and {provider_service}",
            test_type=TestType.CONTRACT,
            test_cases=test_cases
        )

        return await self.run_test_suite(suite)

    async def _execute_test_case(self, test_case: TestCase) -> TestResult:
        """Execute a single test case."""
        start_time = time.time()

        try:
            # Get service base URL
            service_info = await self.catalog_manager.get_service_details(test_case.service_name)
            base_url = service_info.get("base_url", f"http://{test_case.service_name}:8000") if service_info else f"http://{test_case.service_name}:8000"

            # Construct full URL
            url = f"{base_url.rstrip('/')}{test_case.endpoint}"

            # Prepare request
            headers = {"User-Agent": "IntegrationTester/1.0", **test_case.headers}

            # Execute request
            async with self.session.request(
                test_case.method,
                url,
                headers=headers,
                params=test_case.params,
                json=test_case.data if isinstance(test_case.data, dict) else None,
                data=test_case.data if not isinstance(test_case.data, dict) else None,
                timeout=aiohttp.ClientTimeout(total=test_case.timeout)
            ) as response:
                response_status = response.status
                response_data = await response.text()

                # Try to parse JSON
                try:
                    response_data = json.loads(response_data)
                except (json.JSONDecodeError, TypeError):
                    pass  # Keep as string

                # Validate response
                validation_errors = []

                # Status code validation
                if response_status != test_case.expected_status:
                    validation_errors.append(
                        f"Expected status {test_case.expected_status}, got {response_status}"
                    )

                # Schema validation
                if test_case.expected_response_schema:
                    try:
                        import jsonschema
                        jsonschema.validate(response_data, test_case.expected_response_schema)
                    except Exception as e:
                        validation_errors.append(f"Schema validation failed: {e}")

                # Custom validation rules
                for validation_rule in test_case.validation_rules:
                    try:
                        errors = await validation_rule(response_data, response_status)
                        validation_errors.extend(errors)
                    except Exception as e:
                        validation_errors.append(f"Validation rule failed: {e}")

                # Determine test status
                if validation_errors:
                    status = TestStatus.FAILED
                else:
                    status = TestStatus.PASSED

                duration = time.time() - start_time

                return TestResult(
                    test_case=test_case,
                    status=status,
                    duration=duration,
                    response_status=response_status,
                    response_data=response_data,
                    validation_errors=validation_errors,
                    metadata={"url": url}
                )

        except asyncio.TimeoutError:
            return TestResult(
                test_case=test_case,
                status=TestStatus.ERROR,
                duration=time.time() - start_time,
                error_message="Request timeout"
            )
        except Exception as e:
            return TestResult(
                test_case=test_case,
                status=TestStatus.ERROR,
                duration=time.time() - start_time,
                error_message=str(e)
            )

    def _generate_sample_value(self, schema: Dict[str, Any]) -> Any:
        """Generate a sample value from JSON schema."""
        schema_type = schema.get("type", "string")

        if schema_type == "string":
            return "sample_value"
        elif schema_type == "integer":
            return 42
        elif schema_type == "number":
            return 3.14
        elif schema_type == "boolean":
            return True
        elif schema_type == "array":
            return []
        elif schema_type == "object":
            return {}
        else:
            return "sample"

    def _generate_sample_data(self, schema: Dict[str, Any]) -> Any:
        """Generate sample data from JSON schema."""
        if "example" in schema:
            return schema["example"]

        schema_type = schema.get("type", "object")

        if schema_type == "object":
            sample = {}
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                sample[prop_name] = self._generate_sample_value(prop_schema)
            return sample
        else:
            return self._generate_sample_value(schema)

    def _generate_edge_cases(self, base_test: TestCase, operation: Dict[str, Any]) -> List[TestCase]:
        """Generate edge case tests."""
        edge_cases = []

        # Missing required parameters
        if "parameters" in operation:
            for param in operation["parameters"]:
                if param.get("required", False):
                    edge_case = TestCase(
                        name=f"{base_test.name}_missing_{param['name']}",
                        service_name=base_test.service_name,
                        endpoint=base_test.endpoint,
                        method=base_test.method,
                        expected_status=400,  # Bad request
                        params={k: v for k, v in base_test.params.items() if k != param["name"]}
                    )
                    edge_cases.append(edge_case)

        # Invalid data types
        if base_test.data and isinstance(base_test.data, dict):
            for key, value in base_test.data.items():
                if isinstance(value, str):
                    invalid_data = base_test.data.copy()
                    invalid_data[key] = 123  # Invalid type
                    edge_case = TestCase(
                        name=f"{base_test.name}_invalid_{key}_type",
                        service_name=base_test.service_name,
                        endpoint=base_test.endpoint,
                        method=base_test.method,
                        data=invalid_data,
                        expected_status=400
                    )
                    edge_cases.append(edge_case)

        return edge_cases

    def _response_satisfies_contract(
        self,
        provider_response: Dict[str, Any],
        consumer_response: Dict[str, Any]
    ) -> bool:
        """Check if provider response satisfies consumer contract."""
        # Simplified contract checking
        # In a real implementation, this would do detailed schema compatibility checking

        provider_schema = provider_response.get("content", {}).get("application/json", {}).get("schema")
        consumer_schema = consumer_response.get("content", {}).get("application/json", {}).get("schema")

        if not provider_schema or not consumer_schema:
            return True  # Can't validate without schemas

        # Basic compatibility check
        provider_type = provider_schema.get("type")
        consumer_type = consumer_schema.get("type")

        return provider_type == consumer_type

    async def _get_service_spec(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get OpenAPI specification for a service."""
        try:
            service_info = await self.catalog_manager.get_service_details(service_name)
            return service_info.get("openapi_spec") if service_info else None
        except Exception:
            return None
