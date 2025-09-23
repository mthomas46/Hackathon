"""Chaos Engineering Tests for Secure Analyzer Service.

This module tests security scanning resilience and failure scenarios including:
- Network failures during security scanning
- Database connectivity issues during scan storage
- External security service failures
- Resource exhaustion during intensive scanning
- Data corruption during security analysis
- Concurrent scanning with failure injection

Chaos tests ensure the Secure Analyzer service maintains security guarantees under failure conditions.
"""

import asyncio
import time
import random
import json
from typing import Dict, Any, List, Optional
from unittest.mock import patch, AsyncMock, MagicMock, side_effect
from datetime import datetime, timedelta

import pytest


class TestSecurityFailureScenarios:
    """Chaos engineering tests for security scanning under failure conditions."""

    @pytest.fixture
    def chaos_config(self):
        """Chaos test configuration for security scanning."""
        return {
            "failure_rate": 0.15,  # 15% of operations fail (higher for security)
            "scan_timeout_scenarios": [30, 60, 120],  # Different timeout values
            "concurrent_failures": 3,
            "memory_pressure_mb": 150,
            "network_failure_rate": 0.1,
            "database_failure_rate": 0.05
        }

    @pytest.mark.asyncio
    async def test_security_scanning_resilience_under_network_failures(self, chaos_config):
        """Test security scanning resilience against network failures."""
        scan_results = []
        failure_count = 0
        success_count = 0

        async def failing_security_scan(target: str, scan_type: str) -> Dict[str, Any]:
            """Simulate security scan that can fail due to network issues."""
            if random.random() < chaos_config["network_failure_rate"]:
                nonlocal failure_count
                failure_count += 1

                # Simulate different network failure types
                failure_types = [
                    ConnectionError("Network timeout during security scan"),
                    OSError("DNS resolution failed for security service"),
                    Exception("SSL certificate validation failed")
                ]
                raise random.choice(failure_types)
            else:
                nonlocal success_count
                success_count += 1

                # Simulate successful security scan with delay
                delay = random.uniform(0.1, 1.0)
                await asyncio.sleep(delay)

                return {
                    "target": target,
                    "scan_type": scan_type,
                    "vulnerabilities_found": random.randint(0, 5),
                    "severity": random.choice(["low", "medium", "high", "critical"]),
                    "scan_duration": delay,
                    "status": "completed"
                }

        # Perform concurrent security scans with network failures
        targets = [f"service_{i}" for i in range(20)]
        scan_types = ["dependency_check", "secrets_scan", "config_audit"]

        tasks = []
        for target in targets:
            scan_type = random.choice(scan_types)
            task = failing_security_scan(target, scan_type)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        exceptions = [r for r in results if isinstance(r, Exception)]
        successful_scans = [r for r in results if isinstance(r, dict)]

        success_rate = len(successful_scans) / len(results)
        failure_rate = len(exceptions) / len(results)

        print(f"Security Scanning Network Resilience Test:")
        print(f"  Total Scans: {len(results)}")
        print(f"  Successful: {len(successful_scans)}")
        print(f"  Failed: {len(exceptions)}")
        print(f"  Success Rate: {success_rate:.2%}")
        print(f"  Failure Rate: {failure_rate:.2%}")

        # Security scanning should be resilient but thorough
        assert len(exceptions) > 0, "No network failures occurred - chaos test ineffective"
        assert success_rate > 0.75, f"Success rate too low under network chaos: {success_rate:.2%}"

        # Verify scan results integrity
        for scan in successful_scans:
            assert "target" in scan
            assert "scan_type" in scan
            assert "vulnerabilities_found" in scan
            assert scan["status"] == "completed"

    @pytest.mark.asyncio
    async def test_database_failures_during_scan_storage(self, chaos_config):
        """Test handling of database failures during security scan result storage."""
        stored_scans = []
        storage_failures = 0

        class FailingDatabase:
            def __init__(self, failure_rate: float):
                self.failure_rate = failure_rate
                self.connection_lost = False

            async def store_scan_result(self, scan_result: Dict[str, Any]) -> bool:
                if random.random() < self.failure_rate or self.connection_lost:
                    nonlocal storage_failures
                    storage_failures += 1

                    # Simulate database connection loss after some failures
                    if storage_failures > 3:
                        self.connection_lost = True

                    raise Exception("Database connection failed during scan storage")
                else:
                    stored_scans.append(scan_result)
                    return True

        db = FailingDatabase(chaos_config["database_failure_rate"])

        # Simulate storing security scan results with database failures
        scan_results = [
            {
                "scan_id": f"scan_{i}",
                "target": f"service_{i}",
                "vulnerabilities": [
                    {"severity": "high", "description": f"Critical issue {j}"}
                    for j in range(random.randint(0, 3))
                ],
                "timestamp": datetime.now().isoformat()
            }
            for i in range(25)
        ]

        storage_tasks = []
        for scan_result in scan_results:
            task = db.store_scan_result(scan_result)
            storage_tasks.append(task)

        # Execute storage operations with failures
        results = await asyncio.gather(*storage_tasks, return_exceptions=True)

        successful_stores = sum(1 for r in results if not isinstance(r, Exception))
        failed_stores = sum(1 for r in results if isinstance(r, Exception))

        success_rate = successful_stores / len(results)

        print(f"Database Failure During Storage Test:")
        print(f"  Total Storage Attempts: {len(results)}")
        print(f"  Successful: {successful_stores}")
        print(f"  Failed: {failed_stores}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Should handle database failures gracefully
        assert failed_stores > 0, "No database failures occurred - chaos test ineffective"
        assert successful_stores > 0, "All storage operations failed - system unusable"
        assert success_rate > 0.7, f"Storage success rate too low: {success_rate:.2%}"

    @pytest.mark.asyncio
    async def test_external_security_service_failures(self, chaos_config):
        """Test handling of external security service failures."""
        service_failures = {
            "vulnerability_db": 0,
            "malware_scanner": 0,
            "threat_intelligence": 0,
            "code_analysis_service": 0
        }

        async def call_external_security_service(service_name: str, scan_data: Dict[str, Any]) -> Dict[str, Any]:
            """Simulate calling external security services that can fail."""
            failure_rates = {
                "vulnerability_db": 0.1,
                "malware_scanner": 0.15,
                "threat_intelligence": 0.05,
                "code_analysis_service": 0.08
            }

            if random.random() < failure_rates.get(service_name, 0.1):
                service_failures[service_name] += 1
                raise Exception(f"External service {service_name} unavailable")

            # Simulate service response time
            delay = random.uniform(0.2, 1.5)
            await asyncio.sleep(delay)

            return {
                "service": service_name,
                "result": f"Analysis completed for {scan_data.get('target', 'unknown')}",
                "confidence": random.uniform(0.7, 0.95),
                "processing_time": delay
            }

        # Perform security analysis using multiple external services
        scan_targets = [f"component_{i}" for i in range(15)]
        external_services = ["vulnerability_db", "malware_scanner", "threat_intelligence", "code_analysis_service"]

        analysis_tasks = []
        for target in scan_targets:
            for service in external_services:
                scan_data = {"target": target, "scan_type": "comprehensive"}
                task = call_external_security_service(service, scan_data)
                analysis_tasks.append(task)

        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

        # Analyze results
        successful_analyses = [r for r in results if isinstance(r, dict)]
        failed_analyses = [r for r in results if isinstance(r, Exception)]

        success_rate = len(successful_analyses) / len(results)

        print(f"External Security Service Failure Test:")
        print(f"  Total Service Calls: {len(results)}")
        print(f"  Successful: {len(successful_analyses)}")
        print(f"  Failed: {len(failed_analyses)}")
        print(f"  Success Rate: {success_rate:.2%}")
        print(f"  Service Failures: {service_failures}")

        # Should handle external service failures gracefully
        assert sum(service_failures.values()) > 0, "No external service failures - chaos test ineffective"
        assert success_rate > 0.8, f"External service success rate too low: {success_rate:.2%}"

    @pytest.mark.asyncio
    async def test_resource_exhaustion_during_security_scanning(self, chaos_config):
        """Test handling of resource exhaustion during intensive security scanning."""
        import psutil
        import gc

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate intensive security scanning with memory pressure
        async def intensive_security_scan(scan_id: int) -> Dict[str, Any]:
            """Perform intensive security scan that consumes resources."""
            # Create memory pressure during scan
            scan_data = []

            # Simulate processing large amounts of security data
            for i in range(1000):
                scan_data.append({
                    "vulnerability_id": f"VULN-{scan_id}-{i}",
                    "severity": random.choice(["low", "medium", "high", "critical"]),
                    "description": f"Security issue description {i}" * 10,  # Large strings
                    "code_location": f"file_{scan_id}.py:line_{i}",
                    "recommendation": f"Fix recommendation {i}" * 5,
                    "metadata": {"scan_time": datetime.now().isoformat(), "complex_data": [1] * 100}
                })

                # Periodic cleanup attempt
                if i % 100 == 0:
                    await asyncio.sleep(0.001)  # Allow event loop to process

            # Simulate analysis time
            analysis_delay = random.uniform(0.1, 0.5)
            await asyncio.sleep(analysis_delay)

            return {
                "scan_id": scan_id,
                "vulnerabilities_found": len(scan_data),
                "scan_duration": analysis_delay,
                "memory_peak": len(scan_data) * 1000  # Rough memory estimate
            }

        # Run multiple intensive scans concurrently
        scan_tasks = [intensive_security_scan(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = final_memory - initial_memory

        # Force garbage collection
        gc.collect()
        after_gc_memory = process.memory_info().rss / 1024 / 1024  # MB
        gc_reclaimed = final_memory - after_gc_memory

        successful_scans = [r for r in results if isinstance(r, dict)]
        failed_scans = [r for r in results if isinstance(r, Exception)]

        print(f"Resource Exhaustion During Security Scanning Test:")
        print(f"  Total Scans: {len(results)}")
        print(f"  Successful: {len(successful_scans)}")
        print(f"  Failed: {len(failed_scans)}")
        print(f"  Initial Memory: {initial_memory:.2f} MB")
        print(f"  Final Memory: {final_memory:.2f} MB")
        print(f"  Memory Delta: {memory_delta:.2f} MB")
        print(f"  GC Reclaimed: {gc_reclaimed:.2f} MB")

        # Should handle resource pressure without complete failure
        assert len(failed_scans) < len(results) * 0.5, "Too many scans failed due to resource exhaustion"
        assert memory_delta < chaos_config["memory_pressure_mb"], f"Memory usage too high: {memory_delta:.2f} MB"

    @pytest.mark.asyncio
    async def test_data_corruption_during_security_analysis(self):
        """Test recovery from data corruption during security analysis."""
        import hashlib

        class DataIntegrityChecker:
            def __init__(self):
                self.checksums = {}

            def protect_scan_data(self, scan_data: Dict[str, Any]) -> str:
                """Protect scan data with integrity check."""
                json_str = json.dumps(scan_data, sort_keys=True)
                checksum = hashlib.sha256(json_str.encode()).hexdigest()
                self.checksums[scan_data.get("scan_id", "unknown")] = checksum
                return json_str

            def verify_scan_integrity(self, scan_data: Dict[str, Any]) -> bool:
                """Verify scan data integrity."""
                scan_id = scan_data.get("scan_id", "unknown")
                if scan_id not in self.checksums:
                    return False

                json_str = json.dumps(scan_data, sort_keys=True)
                current_checksum = hashlib.sha256(json_str.encode()).hexdigest()
                return current_checksum == self.checksums[scan_id]

            def corrupt_scan_data(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
                """Introduce corruption into scan data."""
                corrupted = scan_data.copy()
                # Introduce various types of corruption
                corruption_type = random.choice(["severity", "add_field", "remove_field", "modify_count"])

                if corruption_type == "severity":
                    corrupted["severity"] = "invalid_severity"
                elif corruption_type == "add_field":
                    corrupted["malicious_field"] = "injected_data"
                elif corruption_type == "remove_field":
                    if "vulnerabilities" in corrupted:
                        corrupted.pop("vulnerabilities")
                elif corruption_type == "modify_count":
                    if "vulnerabilities_found" in corrupted:
                        corrupted["vulnerabilities_found"] = -1

                return corrupted

        integrity_checker = DataIntegrityChecker()

        # Generate and protect original scan data
        original_scans = []
        for i in range(10):
            scan_data = {
                "scan_id": f"security_scan_{i}",
                "target": f"service_{i}",
                "vulnerabilities_found": random.randint(0, 5),
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "scan_timestamp": datetime.now().isoformat(),
                "vulnerabilities": [
                    {
                        "id": f"VULN-{i}-{j}",
                        "title": f"Security Issue {j}",
                        "severity": random.choice(["low", "medium", "high", "critical"])
                    }
                    for j in range(random.randint(0, 3))
                ]
            }
            integrity_checker.protect_scan_data(scan_data)
            original_scans.append(scan_data)

        # Introduce corruption and test detection
        corruption_tests = []
        for original_scan in original_scans:
            corrupted_scan = integrity_checker.corrupt_scan_data(original_scan)
            is_integrity_maintained = integrity_checker.verify_scan_integrity(corrupted_scan)
            corruption_tests.append({
                "scan_id": original_scan["scan_id"],
                "corrupted": not is_integrity_maintained,
                "original_vulns": original_scan["vulnerabilities_found"],
                "corrupted_vulns": corrupted_scan.get("vulnerabilities_found", 0)
            })

        detected_corruptions = sum(1 for test in corruption_tests if test["corrupted"])
        corruption_detection_rate = detected_corruptions / len(corruption_tests)

        print(f"Data Corruption During Security Analysis Test:")
        print(f"  Total Scans: {len(corruption_tests)}")
        print(f"  Corruptions Detected: {detected_corruptions}")
        print(f"  Detection Rate: {corruption_detection_rate:.2%}")

        # Should detect data corruption effectively
        assert corruption_detection_rate > 0.8, f"Poor corruption detection: {corruption_detection_rate:.2%}"

    @pytest.mark.asyncio
    async def test_concurrent_scanning_with_failure_injection(self, chaos_config):
        """Test concurrent security scanning with systematic failure injection."""
        async def concurrent_security_scan(scan_id: int, failure_injection: Dict[str, Any]) -> Dict[str, Any]:
            """Perform security scan with injected failures."""
            start_time = time.time()

            try:
                # Inject failures based on configuration
                if failure_injection.get("network_failure") and random.random() < 0.1:
                    await asyncio.sleep(2.0)  # Timeout
                    raise Exception("Network timeout during scan")

                if failure_injection.get("processing_failure") and random.random() < 0.05:
                    raise Exception("Processing error during security analysis")

                # Simulate scan processing time
                processing_time = random.uniform(0.2, 1.0)
                await asyncio.sleep(processing_time)

                # Generate scan results
                vulnerabilities = []
                vuln_count = random.randint(0, 3)
                for i in range(vuln_count):
                    vulnerabilities.append({
                        "id": f"VULN-{scan_id}-{i}",
                        "severity": random.choice(["low", "medium", "high", "critical"]),
                        "title": f"Security vulnerability {i}"
                    })

                return {
                    "scan_id": scan_id,
                    "status": "completed",
                    "vulnerabilities_found": vuln_count,
                    "vulnerabilities": vulnerabilities,
                    "processing_time": processing_time,
                    "total_time": time.time() - start_time
                }

            except Exception as e:
                return {
                    "scan_id": scan_id,
                    "status": "failed",
                    "error": str(e),
                    "processing_time": time.time() - start_time
                }

        # Configure failure injection for concurrent scanning
        failure_injection = {
            "network_failure": True,
            "processing_failure": True,
            "resource_exhaustion": False
        }

        # Run concurrent security scans
        scan_count = 25
        scan_tasks = [
            concurrent_security_scan(i, failure_injection)
            for i in range(scan_count)
        ]

        results = await asyncio.gather(*tasks)

        # Analyze concurrent scanning results
        completed_scans = [r for r in results if r["status"] == "completed"]
        failed_scans = [r for r in results if r["status"] == "failed"]

        completion_rate = len(completed_scans) / len(results)

        total_vulnerabilities = sum(scan.get("vulnerabilities_found", 0) for scan in completed_scans)
        avg_processing_time = sum(scan.get("processing_time", 0) for scan in results) / len(results)

        print(f"Concurrent Scanning with Failure Injection Test:")
        print(f"  Total Scans: {len(results)}")
        print(f"  Completed: {len(completed_scans)}")
        print(f"  Failed: {len(failed_scans)}")
        print(f"  Completion Rate: {completion_rate:.2%}")
        print(f"  Total Vulnerabilities Found: {total_vulnerabilities}")
        print(f"  Average Processing Time: {avg_processing_time:.2f}s")

        # Concurrent scanning should maintain reasonable success rate under failure conditions
        assert completion_rate > 0.75, f"Completion rate too low under concurrent failures: {completion_rate:.2%}"
        assert len(failed_scans) > 0, "No failures occurred - chaos test ineffective"

    def test_security_policy_enforcement_under_failure(self):
        """Test that security policies are maintained even during failures."""
        security_policy_violations = []

        class SecurityPolicyEnforcer:
            def __init__(self):
                self.policies = {
                    "max_scan_time": 300,  # 5 minutes
                    "max_vulnerabilities_per_scan": 100,
                    "require_encryption": True,
                    "audit_all_actions": True
                }

            def enforce_scan_policies(self, scan_request: Dict[str, Any]) -> Dict[str, Any]:
                """Enforce security policies on scan requests."""
                violations = []

                # Check scan time limits
                if scan_request.get("timeout", 0) > self.policies["max_scan_time"]:
                    violations.append("Scan timeout exceeds maximum allowed")

                # Validate encryption requirements
                if not scan_request.get("encrypted", False) and self.policies["require_encryption"]:
                    violations.append("Encryption required but not enabled")

                # Check for proper authentication
                if not scan_request.get("authenticated", False):
                    violations.append("Authentication required for security scans")

                if violations:
                    security_policy_violations.extend(violations)
                    return {"allowed": False, "violations": violations}
                else:
                    return {"allowed": True, "violations": []}

        enforcer = SecurityPolicyEnforcer()

        # Test policy enforcement with various scan requests
        test_requests = [
            # Valid request
            {"timeout": 120, "encrypted": True, "authenticated": True},
            # Invalid requests
            {"timeout": 600, "encrypted": True, "authenticated": True},  # Too long
            {"timeout": 120, "encrypted": False, "authenticated": True},  # No encryption
            {"timeout": 120, "encrypted": True, "authenticated": False},  # No auth
            {"timeout": 800, "encrypted": False, "authenticated": False},  # Multiple violations
        ]

        policy_results = []
        for request in test_requests:
            result = enforcer.enforce_scan_policies(request)
            policy_results.append(result)

        allowed_requests = sum(1 for r in policy_results if r["allowed"])
        blocked_requests = sum(1 for r in policy_results if not r["allowed"])

        print(f"Security Policy Enforcement Under Failure Test:")
        print(f"  Total Requests: {len(test_requests)}")
        print(f"  Allowed: {allowed_requests}")
        print(f"  Blocked: {blocked_requests}")
        print(f"  Policy Violations: {len(security_policy_violations)}")

        # Should block requests that violate security policies
        assert blocked_requests > 0, "No requests blocked - policy enforcement not working"
        assert allowed_requests > 0, "All requests blocked - policy too restrictive"
        assert len(security_policy_violations) > 0, "No policy violations detected"

    @pytest.mark.asyncio
    async def test_circuit_breaker_for_security_services(self):
        """Test circuit breaker pattern for external security services."""
        class SecurityServiceCircuitBreaker:
            def __init__(self, failure_threshold: int = 3):
                self.failure_threshold = failure_threshold
                self.failure_count = 0
                self.state = "closed"  # closed, open, half_open
                self.last_failure_time = None
                self.success_count = 0

            async def call_security_service(self, service_call) -> Any:
                if self.state == "open":
                    # Allow limited traffic in half-open state after timeout
                    if time.time() - self.last_failure_time > 30:  # 30 second timeout
                        self.state = "half_open"
                    else:
                        raise Exception("Security service circuit breaker is OPEN")

                try:
                    result = await service_call()
                    self._on_success()
                    return result
                except Exception as e:
                    self._on_failure()
                    raise e

            def _on_success(self):
                if self.state == "half_open":
                    self.state = "closed"
                    self.failure_count = 0
                    self.success_count += 1

            def _on_failure(self):
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "open"

        circuit_breaker = SecurityServiceCircuitBreaker()

        # Simulate calling external security service with failures
        call_count = 0
        async def failing_security_service_call():
            nonlocal call_count
            call_count += 1

            # Service fails 70% of the time
            if random.random() < 0.7:
                raise Exception(f"Security service call {call_count} failed")
            else:
                return {"result": "security_analysis_complete", "call": call_count}

        # Make multiple service calls through circuit breaker
        results = []
        for i in range(15):
            try:
                result = await circuit_breaker.call_security_service(failing_security_service_call)
                results.append({"attempt": i, "status": "success", "result": result})
            except Exception as e:
                results.append({"attempt": i, "status": "failed", "error": str(e)})

        successful_calls = sum(1 for r in results if r["status"] == "success")
        failed_calls = sum(1 for r in results if r["status"] == "failed")

        print(f"Security Service Circuit Breaker Test:")
        print(f"  Total Calls: {len(results)}")
        print(f"  Successful: {successful_calls}")
        print(f"  Failed: {failed_calls}")
        print(f"  Circuit Breaker State: {circuit_breaker.state}")

        # Circuit breaker should prevent cascade of failures
        assert failed_calls > 0, "No failures occurred - circuit breaker not tested"
        assert successful_calls < len(results), "No failures blocked - circuit breaker ineffective"
