#!/usr/bin/env python3
"""
Health Check Endpoint Validator
===============================

Automated health check endpoint validation system for the ecosystem.
Validates all service health endpoints, response formats, and reliability.

Features:
- Automatic endpoint discovery from Docker Compose
- Comprehensive health check validation
- Response format standardization
- Performance monitoring
- Integration with CI/CD pipelines
- Detailed reporting and analytics

Author: Ecosystem Hardening Framework
"""

import json
import time
import asyncio
import aiohttp
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from urllib.parse import urljoin, urlparse
import statistics
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HealthEndpoint:
    """Represents a health check endpoint"""
    service_name: str
    url: str
    expected_status: int = 200
    expected_fields: List[str] = field(default_factory=lambda: ["status"])
    timeout: int = 3  # Reduced from 10 to 3 seconds to prevent hanging
    retries: int = 1  # Reduced from 3 to 1 retry to speed up validation
    interval: int = 30


@dataclass
class HealthCheckResult:
    """Result of a health check validation"""
    endpoint: HealthEndpoint
    success: bool
    response_time: float
    status_code: Optional[int]
    response_body: Optional[Dict[str, Any]]
    error_message: Optional[str]
    timestamp: float = field(default_factory=time.time)
    attempts: int = 1


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    total_endpoints: int
    successful_checks: int
    failed_checks: int
    total_response_time: float
    average_response_time: float
    min_response_time: float
    max_response_time: float
    availability_percentage: float
    detailed_results: List[HealthCheckResult]
    critical_failures: List[HealthCheckResult]
    recommendations: List[str]
    validation_timestamp: float = field(default_factory=time.time)


class HealthEndpointValidator:
    """
    Automated health check endpoint validator.

    This class provides comprehensive validation of service health endpoints,
    including automatic discovery, testing, and reporting.
    """

    def __init__(self, workspace_path: Optional[str] = None, timeout: int = 2, retries: int = 1):
        """Initialize the health endpoint validator"""
        self.workspace_path = Path(workspace_path or Path.cwd())
        self.endpoints: List[HealthEndpoint] = []
        self.results: List[HealthCheckResult] = []
        self.docker_compose_path = self.workspace_path / "docker-compose.dev.yml"
        self.reports_dir = self.workspace_path / "reports" / "health_validation"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Default timeout and retries for faster execution - reduced to prevent hanging
        self.default_timeout = timeout
        self.default_retries = retries

        # Standard health check patterns
        self.standard_health_fields = [
            "status", "service", "timestamp", "version", "uptime",
            "dependencies", "health", "ready", "alive"
        ]

        logger.info("🔍 Health Endpoint Validator initialized")

    def discover_endpoints(self) -> List[HealthEndpoint]:
        """
        Automatically discover health check endpoints from Docker Compose configuration.

        Returns:
            List of discovered HealthEndpoint objects
        """
        logger.info("🔍 Discovering health check endpoints...")

        if not self.docker_compose_path.exists():
            logger.error(f"❌ Docker Compose file not found: {self.docker_compose_path}")
            return []

        try:
            with open(self.docker_compose_path, 'r') as f:
                compose_config = yaml.safe_load(f)

            if 'services' not in compose_config:
                logger.error("❌ No services found in Docker Compose configuration")
                return []

            endpoints = []

            for service_name, service_config in compose_config['services'].items():
                # Skip Redis as it doesn't have HTTP health endpoints
                if service_name == 'redis':
                    logger.info(f"ℹ️ Skipping Redis service - uses Redis protocol, not HTTP")
                    continue

                # Extract port mapping
                ports = service_config.get('ports', [])
                if not ports:
                    logger.warning(f"⚠️ No ports configured for service: {service_name}")
                    continue

                # Get the first port mapping (external:internal)
                port_mapping = ports[0]
                if isinstance(port_mapping, str):
                    # Format: "external:internal"
                    external_port = port_mapping.split(':')[0]
                elif isinstance(port_mapping, dict):
                    # Format: {"published": external, "target": internal}
                    external_port = port_mapping.get('published', port_mapping.get('target'))
                else:
                    external_port = port_mapping

                try:
                    external_port = int(external_port)
                except (ValueError, TypeError):
                    logger.warning(f"⚠️ Invalid port mapping for {service_name}: {port_mapping}")
                    continue

                # Construct health check URL
                health_url = f"http://localhost:{external_port}/health"

                # Create endpoint with service-specific expectations and faster defaults
                endpoint = HealthEndpoint(
                    service_name=service_name,
                    url=health_url,
                    expected_fields=self._get_expected_fields(service_name),
                    timeout=self.default_timeout,
                    retries=self.default_retries
                )

                endpoints.append(endpoint)
                logger.info(f"✅ Discovered endpoint: {service_name} -> {health_url}")

            self.endpoints = endpoints
            logger.info(f"🔍 Discovered {len(endpoints)} health check endpoints")
            return endpoints

        except Exception as e:
            logger.error(f"❌ Error discovering endpoints: {e}")
            return []

    def _get_expected_fields(self, service_name: str) -> List[str]:
        """Get expected health check fields based on service type"""
        base_fields = ["status"]

        # Service-specific expectations
        service_expectations = {
            "redis": ["status", "ping_response"],
            "llm-gateway": ["status", "service", "ollama_available"],
            "doc_store": ["status", "service", "database_connected"],
            "orchestrator": ["status", "service", "workflows_loaded"],
            "mock-data-generator": ["status", "service", "data_sources"],
            "source-agent": ["status", "service", "doc_store_connected"],
            "code-analyzer": ["status", "service", "analysis_ready"],
            "notification-service": ["status", "service", "email_configured"],
            "frontend": ["status", "service", "api_connected"],
            "analysis-service": ["status", "service", "models_loaded"],
            "prompt-store": ["status", "service", "database_connected"],
            "summarizer-hub": ["status", "service", "llm_connected"]
        }

        return service_expectations.get(service_name, base_fields)

    async def validate_endpoint_async(self, endpoint: HealthEndpoint) -> HealthCheckResult:
        """
        Validate a single health check endpoint asynchronously.

        Args:
            endpoint: HealthEndpoint to validate

        Returns:
            HealthCheckResult with validation details
        """
        start_time = time.time()

        for attempt in range(endpoint.retries):
            try:
                timeout = aiohttp.ClientTimeout(total=endpoint.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(endpoint.url) as response:
                        response_time = time.time() - start_time
                        status_code = response.status

                        try:
                            response_body = await response.json()
                        except:
                            response_body = {"raw_response": await response.text()}

                        # Validate response
                        success = self._validate_response(endpoint, status_code, response_body)

                        if success or attempt == endpoint.retries - 1:
                            return HealthCheckResult(
                                endpoint=endpoint,
                                success=success,
                                response_time=response_time,
                                status_code=status_code,
                                response_body=response_body,
                                error_message=None if success else "Validation failed",
                                attempts=attempt + 1
                            )

            except aiohttp.ClientError as e:
                if attempt == endpoint.retries - 1:
                    response_time = time.time() - start_time
                    return HealthCheckResult(
                        endpoint=endpoint,
                        success=False,
                        response_time=response_time,
                        status_code=None,
                        response_body=None,
                        error_message=f"Connection error: {str(e)}",
                        attempts=attempt + 1
                    )
            except Exception as e:
                if attempt == endpoint.retries - 1:
                    response_time = time.time() - start_time
                    return HealthCheckResult(
                        endpoint=endpoint,
                        success=False,
                        response_time=response_time,
                        status_code=None,
                        response_body=None,
                        error_message=f"Unexpected error: {str(e)}",
                        attempts=attempt + 1
                    )

            # Wait before retry
            if attempt < endpoint.retries - 1:
                await asyncio.sleep(endpoint.interval)

        # This should never be reached, but just in case
        return HealthCheckResult(
            endpoint=endpoint,
            success=False,
            response_time=time.time() - start_time,
            status_code=None,
            response_body=None,
            error_message="Max retries exceeded",
            attempts=endpoint.retries
        )

    def _validate_response(self, endpoint: HealthEndpoint, status_code: int,
                          response_body: Dict[str, Any]) -> bool:
        """
        Validate the health check response.

        Args:
            endpoint: The health endpoint
            status_code: HTTP status code
            response_body: Parsed JSON response

        Returns:
            True if validation passes, False otherwise
        """
        # Check status code
        if status_code != endpoint.expected_status:
            logger.warning(f"⚠️ Status code mismatch for {endpoint.service_name}: "
                         f"expected {endpoint.expected_status}, got {status_code}")
            return False

        # Check required fields
        if not isinstance(response_body, dict):
            logger.warning(f"⚠️ Invalid response format for {endpoint.service_name}: "
                         "expected JSON object")
            return False

        missing_fields = []
        for field in endpoint.expected_fields:
            if field not in response_body:
                missing_fields.append(field)

        if missing_fields:
            logger.warning(f"⚠️ Missing fields in {endpoint.service_name} response: {missing_fields}")
            return False

        # Validate status field if present
        if "status" in response_body:
            status_value = response_body["status"]
            if isinstance(status_value, str):
                # Common status values
                valid_statuses = ["healthy", "ok", "up", "ready", "alive"]
                if status_value.lower() not in valid_statuses:
                    logger.warning(f"⚠️ Invalid status value for {endpoint.service_name}: {status_value}")
                    return False

        logger.debug(f"✅ Health check passed for {endpoint.service_name}")
        return True

    async def validate_all_endpoints_async(self) -> ValidationReport:
        """
        Validate all discovered health check endpoints asynchronously.

        Returns:
            Comprehensive ValidationReport
        """
        logger.info("🔍 Starting comprehensive health endpoint validation...")

        if not self.endpoints:
            logger.warning("⚠️ No endpoints to validate")
            return self._create_empty_report()

        # Run all validations concurrently
        tasks = [self.validate_endpoint_async(endpoint) for endpoint in self.endpoints]
        self.results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(self.results):
            if isinstance(result, Exception):
                # Create failed result for exceptions
                endpoint = self.endpoints[i] if i < len(self.endpoints) else None
                if endpoint:
                    processed_results.append(HealthCheckResult(
                        endpoint=endpoint,
                        success=False,
                        response_time=0.0,
                        status_code=None,
                        response_body=None,
                        error_message=f"Validation exception: {str(result)}"
                    ))
            else:
                processed_results.append(result)

        self.results = processed_results

        # Generate report
        return self._generate_report()

    def validate_all_endpoints_sync(self) -> ValidationReport:
        """
        Validate all discovered health check endpoints synchronously.

        Returns:
            Comprehensive ValidationReport
        """
        logger.info("🔍 Starting synchronous health endpoint validation...")

        async def run_async():
            return await self.validate_all_endpoints_async()

        return asyncio.run(run_async())

    def _generate_report(self) -> ValidationReport:
        """
        Generate comprehensive validation report from results.

        Returns:
            ValidationReport with detailed analysis
        """
        if not self.results:
            return self._create_empty_report()

        # Calculate statistics
        successful_checks = sum(1 for result in self.results if result.success)
        failed_checks = len(self.results) - successful_checks

        response_times = [r.response_time for r in self.results if r.response_time > 0]
        total_response_time = sum(response_times) if response_times else 0
        average_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0

        availability_percentage = (successful_checks / len(self.results)) * 100 if self.results else 0

        # Identify critical failures
        critical_failures = [r for r in self.results if not r.success]

        # Generate recommendations
        recommendations = self._generate_recommendations()

        report = ValidationReport(
            total_endpoints=len(self.results),
            successful_checks=successful_checks,
            failed_checks=failed_checks,
            total_response_time=total_response_time,
            average_response_time=average_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            availability_percentage=availability_percentage,
            detailed_results=self.results,
            critical_failures=critical_failures,
            recommendations=recommendations
        )

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        if not self.results:
            return recommendations

        successful_checks = sum(1 for result in self.results if result.success)
        availability_percentage = (successful_checks / len(self.results)) * 100

        # Availability recommendations
        if availability_percentage < 95:
            recommendations.append("🔴 CRITICAL: Service availability is below 95% - investigate failed services immediately")
        elif availability_percentage < 99:
            recommendations.append("🟡 WARNING: Service availability is below 99% - monitor closely")

        # Performance recommendations
        response_times = [r.response_time for r in self.results if r.response_time > 0]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            if avg_response_time > 5.0:
                recommendations.append("🟡 WARNING: Average response time > 5s - consider performance optimization")
            elif avg_response_time > 2.0:
                recommendations.append("ℹ️ INFO: Average response time > 2s - monitor for performance trends")

        # Specific service recommendations
        for result in self.results:
            if not result.success:
                if "Connection refused" in str(result.error_message or ""):
                    recommendations.append(f"🔴 CRITICAL: {result.endpoint.service_name} is not responding - check if service is running")
                elif "timeout" in str(result.error_message or "").lower():
                    recommendations.append(f"🟡 WARNING: {result.endpoint.service_name} health check timed out - investigate performance")
                else:
                    recommendations.append(f"🟡 WARNING: {result.endpoint.service_name} health check failed - review logs")

        # General recommendations
        if len(self.results) > 0:
            recommendations.append("ℹ️ INFO: Consider implementing circuit breakers for dependent services")
            recommendations.append("ℹ️ INFO: Add health check monitoring to alerting systems")
            recommendations.append("ℹ️ INFO: Implement health check caching to reduce load")

        return recommendations

    def _create_empty_report(self) -> ValidationReport:
        """Create empty report when no validation was performed"""
        return ValidationReport(
            total_endpoints=0,
            successful_checks=0,
            failed_checks=0,
            total_response_time=0.0,
            average_response_time=0.0,
            min_response_time=0.0,
            max_response_time=0.0,
            availability_percentage=0.0,
            detailed_results=[],
            critical_failures=[],
            recommendations=["ℹ️ INFO: No health endpoints were discovered or validated"]
        )

    def print_report(self, report: ValidationReport, verbose: bool = True):
        """
        Print formatted validation report.

        Args:
            report: ValidationReport to print
            verbose: Whether to include detailed results
        """
        print("\n" + "="*70)
        print("🏥 HEALTH ENDPOINT VALIDATION REPORT")
        print("="*70)
        print(f"📊 Total Endpoints: {report.total_endpoints}")
        print(f"✅ Successful: {report.successful_checks}")
        print(f"❌ Failed: {report.failed_checks}")
        print(f"⏱️  Avg Response: {report.average_response_time:.3f}s")
        print(f"📈 Availability: {report.availability_percentage:.1f}%")
        print(f"⚡ Min Response: {report.min_response_time:.3f}s")
        print(f"🐌 Max Response: {report.max_response_time:.3f}s")

        if report.critical_failures:
            print(f"\n🔴 CRITICAL FAILURES ({len(report.critical_failures)}):")
            for failure in report.critical_failures:
                print(f"  • {failure.endpoint.service_name}: {failure.error_message}")

        if verbose and report.detailed_results:
            print("\n📋 DETAILED RESULTS:")
            for result in report.detailed_results:
                status = "✅" if result.success else "❌"
                response_time = f"{result.response_time:.3f}"
                print(f"  {status} {result.endpoint.service_name:<20} "
                      f"{response_time:<8} {result.status_code or 'N/A':<6} "
                      f"{result.attempts} attempts")

        if report.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report.recommendations:
                print(f"  • {rec}")

        print("="*70)

    def save_report(self, report: ValidationReport, filename: Optional[str] = None) -> Path:
        """
        Save validation report to JSON file.

        Args:
            report: ValidationReport to save
            filename: Optional custom filename

        Returns:
            Path to saved report file
        """
        if not filename:
            timestamp = int(time.time())
            filename = f"health_validation_{timestamp}.json"

        report_path = self.reports_dir / filename

        # Convert dataclasses to dictionaries for JSON serialization
        report_dict = {
            "total_endpoints": report.total_endpoints,
            "successful_checks": report.successful_checks,
            "failed_checks": report.failed_checks,
            "total_response_time": report.total_response_time,
            "average_response_time": report.average_response_time,
            "min_response_time": report.min_response_time,
            "max_response_time": report.max_response_time,
            "availability_percentage": report.availability_percentage,
            "validation_timestamp": report.validation_timestamp,
            "detailed_results": [
                {
                    "service_name": r.endpoint.service_name,
                    "url": r.endpoint.url,
                    "success": r.success,
                    "response_time": r.response_time,
                    "status_code": r.status_code,
                    "response_body": r.response_body,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp,
                    "attempts": r.attempts
                }
                for r in report.detailed_results
            ],
            "critical_failures": [
                {
                    "service_name": f.endpoint.service_name,
                    "url": f.endpoint.url,
                    "error_message": f.error_message,
                    "response_time": f.response_time
                }
                for f in report.critical_failures
            ],
            "recommendations": report.recommendations
        }

        with open(report_path, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)

        logger.info(f"💾 Report saved to: {report_path}")
        return report_path

    def validate_with_continuous_monitoring(self, duration_minutes: int = 5,
                                          interval_seconds: int = 30) -> ValidationReport:
        """
        Perform continuous health monitoring for specified duration.

        Args:
            duration_minutes: How long to monitor (minutes)
            interval_seconds: Interval between checks (seconds)

        Returns:
            Consolidated ValidationReport
        """
        logger.info(f"🔄 Starting continuous monitoring for {duration_minutes} minutes...")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        all_results = []

        while time.time() < end_time:
            logger.info("🔍 Running health check cycle...")

            # Discover endpoints (in case services started/stopped)
            self.discover_endpoints()

            # Run validation
            async def run_check():
                tasks = [self.validate_endpoint_async(endpoint) for endpoint in self.endpoints]
                return await asyncio.gather(*tasks, return_exceptions=True)

            results = asyncio.run(run_check())
            all_results.extend(results)

            # Wait for next cycle
            time.sleep(interval_seconds)

        # Process all results
        self.results = []
        for i, result in enumerate(all_results):
            if isinstance(result, Exception):
                # Create failed result for exceptions
                cycle_num = i // len(self.endpoints) if self.endpoints else 0
                endpoint_idx = i % len(self.endpoints) if self.endpoints else 0
                endpoint = self.endpoints[endpoint_idx] if endpoint_idx < len(self.endpoints) else None
                if endpoint:
                    self.results.append(HealthCheckResult(
                        endpoint=endpoint,
                        success=False,
                        response_time=0.0,
                        status_code=None,
                        response_body=None,
                        error_message=f"Monitoring cycle {cycle_num}: {str(result)}"
                    ))
            else:
                self.results.append(result)

        # Generate consolidated report
        report = self._generate_report()
        logger.info(f"🔄 Continuous monitoring completed. {len(all_results)} total checks performed.")

        return report


def main():
    """Main entry point for health endpoint validation"""
    import argparse

    parser = argparse.ArgumentParser(description="Health Endpoint Validator")
    parser.add_argument("--workspace", help="Workspace path")
    parser.add_argument("--mode", choices=["single", "continuous", "discover"],
                       default="single", help="Validation mode")
    parser.add_argument("--duration", type=int, default=5,
                       help="Duration for continuous monitoring (minutes)")
    parser.add_argument("--interval", type=int, default=30,
                       help="Interval between checks for continuous monitoring (seconds)")
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose output")
    parser.add_argument("--save-report", action="store_true",
                       help="Save validation report to file")
    parser.add_argument("--report-file", help="Custom report filename")

    args = parser.parse_args()

    # Initialize validator
    validator = HealthEndpointValidator(args.workspace)

    try:
        if args.mode == "discover":
            # Just discover and list endpoints
            endpoints = validator.discover_endpoints()
            print(f"\n🔍 Discovered {len(endpoints)} health check endpoints:")
            for endpoint in endpoints:
                print(f"  • {endpoint.service_name}: {endpoint.url}")
                print(f"    Expected fields: {endpoint.expected_fields}")
            return 0

        elif args.mode == "continuous":
            # Continuous monitoring
            print(f"🔄 Starting continuous health monitoring for {args.duration} minutes...")
            report = validator.validate_with_continuous_monitoring(
                args.duration, args.interval
            )

        else:
            # Single validation run
            print("🏥 Health Endpoint Validator")
            print("=" * 50)

            # Discover endpoints
            endpoints = validator.discover_endpoints()
            if not endpoints:
                print("❌ No health check endpoints discovered!")
                return 1

            # Run validation
            report = validator.validate_all_endpoints_sync()

        # Print report
        validator.print_report(report, args.verbose)

        # Save report if requested
        if args.save_report:
            report_path = validator.save_report(report, args.report_file)
            print(f"💾 Report saved: {report_path}")

        # Return appropriate exit code
        if report.availability_percentage < 95:
            print("❌ CRITICAL: Service availability below 95%")
            return 1
        elif report.availability_percentage < 99:
            print("⚠️ WARNING: Service availability below 99%")
            return 0
        else:
            print("✅ All health checks passed")
            return 0

    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
