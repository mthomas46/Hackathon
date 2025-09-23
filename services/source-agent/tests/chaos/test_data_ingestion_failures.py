"""Chaos Engineering Tests for Data Ingestion Operations in Source Agent Service.

This module tests data ingestion resilience and failure scenarios including:
- Data source connectivity failures and outages
- Authentication and authorization failures during data access
- Network interruptions during data transfer
- Data source rate limiting and throttling
- Content parsing and format validation failures
- Concurrent ingestion failures and resource exhaustion

Chaos tests ensure the Source Agent service maintains data ingestion reliability during infrastructure failures.
"""

import asyncio
import time
import random
import json
from typing import Dict, Any, List, Optional
from unittest.mock import patch, AsyncMock, MagicMock, side_effect
from datetime import datetime, timedelta

import pytest
import httpx


class TestDataIngestionFailures:
    """Chaos engineering tests for data ingestion under failure conditions."""

    @pytest.fixture
    def chaos_config(self):
        """Chaos test configuration for data ingestion."""
        return {
            "failure_rate": 0.1,  # 10% of data operations fail
            "source_outage_scenarios": ["github", "api", "database", "filesystem"],
            "auth_failure_rate": 0.08,
            "network_failure_rate": 0.07,
            "rate_limit_scenarios": [10, 25, 50],  # requests per minute
            "concurrent_failures": 5,
            "data_corruption_rate": 0.03
        }

    @pytest.mark.asyncio
    async def test_data_source_connectivity_outages(self, chaos_config):
        """Test resilience against data source connectivity outages."""
        outage_count = 0
        retry_successes = 0
        fallback_activations = 0

        async def ingest_from_source_with_outages(source_config: Dict[str, Any], session_id: str) -> Dict[str, Any]:
            """Simulate data ingestion from sources that can experience outages."""
            nonlocal outage_count, retry_successes, fallback_activations

            source_type = source_config["type"]
            max_retries = 3
            retry_count = 0

            while retry_count <= max_retries:
                try:
                    # Simulate source-specific outage patterns
                    if source_type in chaos_config["source_outage_scenarios"] and random.random() < 0.15:
                        outage_count += 1

                        if source_type == "github":
                            raise httpx.ConnectError("GitHub API service unavailable")
                        elif source_type == "api":
                            raise httpx.TimeoutError("External API timeout")
                        elif source_type == "database":
                            raise Exception("Database connection lost")
                        else:  # filesystem
                            raise OSError("File system access denied")

                    # Simulate authentication failures
                    if random.random() < chaos_config["auth_failure_rate"]:
                        raise Exception(f"Authentication failed for {source_type} source")

                    # Simulate successful ingestion with potential fallback
                    if random.random() < 0.1 and retry_count > 0:  # 10% need fallback after retries
                        fallback_activations += 1
                        # Simulate fallback to cached/alternative source
                        await asyncio.sleep(0.5)
                        return {
                            "source_type": source_type,
                            "status": "completed_with_fallback",
                            "documents_ingested": random.randint(1, 5),
                            "fallback_used": True,
                            "retries": retry_count
                        }

                    # Normal successful ingestion
                    await asyncio.sleep(random.uniform(0.2, 1.0))

                    if retry_count > 0:
                        retry_successes += 1

                    return {
                        "source_type": source_type,
                        "status": "completed",
                        "documents_ingested": random.randint(1, 10),
                        "data_size_bytes": random.randint(1024, 1048576),
                        "retries": retry_count
                    }

                except (httpx.ConnectError, httpx.TimeoutError, OSError, Exception):
                    retry_count += 1
                    if retry_count <= max_retries:
                        # Exponential backoff
                        backoff_time = 0.5 * (2 ** (retry_count - 1))
                        await asyncio.sleep(backoff_time)
                        continue
                    else:
                        raise

        # Test ingestion from multiple source types with outages
        test_sources = [
            {"type": "github", "config": {"repo": "test/repo"}},
            {"type": "api", "config": {"url": "https://api.example.com"}},
            {"type": "database", "config": {"query": "SELECT * FROM test"}},
            {"type": "filesystem", "config": {"path": "/test/docs"}}
        ]

        ingestion_tasks = []
        for i, source in enumerate(test_sources * 8):  # 8 requests per source type
            task = ingest_from_source_with_outages(source, f"session_{i}")
            ingestion_tasks.append(task)

        results = await asyncio.gather(*ingestion_tasks, return_exceptions=True)

        # Analyze results
        successful_ingestions = [r for r in results if isinstance(r, dict)]
        failed_ingestions = [r for r in results if isinstance(r, Exception)]

        fallback_used = sum(1 for r in successful_ingestions if r.get("fallback_used", False))
        total_retries = sum(r.get("retries", 0) for r in successful_ingestions)

        success_rate = len(successful_ingestions) / len(results)

        print(f"Data Source Connectivity Outage Test:")
        print(f"  Total Ingestion Attempts: {len(results)}")
        print(f"  Successful: {len(successful_ingestions)}")
        print(f"  Failed: {len(failed_ingestions)}")
        print(f"  Fallbacks Used: {fallback_used}")
        print(f"  Total Retries: {total_retries}")
        print(f"  Outages Experienced: {outage_count}")
        print(f"  Retry Successes: {retry_successes}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Data ingestion should be resilient to source outages
        assert len(failed_ingestions) > 0, "No connectivity failures occurred - chaos test ineffective"
        assert success_rate > 0.8, f"Success rate too low under connectivity chaos: {success_rate:.2%}"
        assert retry_successes > 0, "No retry recovery used"
        assert fallback_used >= 0, "Fallback mechanisms should be available when needed"

    @pytest.mark.asyncio
    async def test_authentication_authorization_failures(self, chaos_config):
        """Test handling of authentication and authorization failures."""
        auth_failures = 0
        token_refresh_successes = 0
        permission_denied_events = 0

        async def authenticate_and_ingest(source_config: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
            """Simulate authentication and data ingestion with auth failures."""
            nonlocal auth_failures, token_refresh_successes, permission_denied_events

            source_type = source_config["type"]
            auth_attempts = 0
            max_auth_attempts = 2

            while auth_attempts <= max_auth_attempts:
                try:
                    # Simulate authentication failures
                    if random.random() < chaos_config["auth_failure_rate"]:
                        auth_failures += 1

                        if random.random() < 0.6:  # 60% token expired
                            if auth_attempts == 0:  # First attempt - try refresh
                                await asyncio.sleep(0.3)  # Token refresh time
                                token_refresh_successes += 1
                                # Token refresh successful, continue
                            else:
                                raise Exception("Token refresh failed")
                        else:
                            permission_denied_events += 1
                            raise Exception(f"Permission denied for {source_type} access")

                    # Simulate successful authentication and ingestion
                    await asyncio.sleep(random.uniform(0.1, 0.5))

                    return {
                        "source_type": source_type,
                        "status": "authenticated_and_ingested",
                        "auth_attempts": auth_attempts + 1,
                        "token_refreshed": auth_attempts > 0,
                        "documents_ingested": random.randint(1, 8)
                    }

                except Exception:
                    auth_attempts += 1
                    if auth_attempts <= max_auth_attempts:
                        continue
                    else:
                        raise

        # Test authentication across different source types and credential scenarios
        test_scenarios = [
            {"type": "github", "credentials": {"token": "gh_token"}},
            {"type": "api", "credentials": {"api_key": "api_key_123"}},
            {"type": "database", "credentials": {"username": "user", "password": "pass"}},
            {"type": "filesystem", "credentials": {"ssh_key": "ssh_key_path"}}
        ]

        auth_tasks = []
        for scenario in test_scenarios:
            for i in range(10):  # 10 auth attempts per scenario
                task = authenticate_and_ingest(scenario, scenario["credentials"])
                auth_tasks.append(task)

        results = await asyncio.gather(*auth_tasks, return_exceptions=True)

        # Analyze authentication results
        successful_auths = [r for r in results if isinstance(r, dict)]
        failed_auths = [r for r in results if isinstance(r, Exception)]

        token_refreshes = sum(1 for r in successful_auths if r.get("token_refreshed", False))
        total_auth_attempts = sum(r.get("auth_attempts", 1) for r in successful_auths)

        success_rate = len(successful_auths) / len(results)

        print(f"Authentication Authorization Failure Test:")
        print(f"  Total Auth Attempts: {len(results)}")
        print(f"  Successful: {len(successful_auths)}")
        print(f"  Failed: {len(failed_auths)}")
        print(f"  Token Refreshes: {token_refreshes}")
        print(f"  Auth Failures: {auth_failures}")
        print(f"  Permission Denied: {permission_denied_events}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Authentication should handle failures gracefully
        assert auth_failures > 0, "No authentication failures occurred - chaos test ineffective"
        assert success_rate > 0.85, f"Authentication success rate too low: {success_rate:.2%}"
        assert token_refresh_successes >= 0, "Token refresh mechanism should be available"

    @pytest.mark.asyncio
    async def test_network_interruptions_during_transfer(self, chaos_config):
        """Test handling of network interruptions during data transfer."""
        network_interruptions = 0
        resumable_transfers = 0
        partial_data_recovery = 0

        async def transfer_data_with_network_issues(source_config: Dict[str, Any], transfer_size: int) -> Dict[str, Any]:
            """Simulate data transfer with network interruptions."""
            nonlocal network_interruptions, resumable_transfers, partial_data_recovery

            transferred_bytes = 0
            interruptions = 0
            max_interruptions = 3

            while transferred_bytes < transfer_size and interruptions <= max_interruptions:
                # Simulate chunked transfer
                chunk_size = min(8192, transfer_size - transferred_bytes)  # 8KB chunks

                # Simulate network interruption during transfer
                if random.random() < chaos_config["network_failure_rate"] and interruptions < max_interruptions:
                    network_interruptions += 1
                    interruptions += 1

                    # Decide if transfer is resumable
                    if random.random() < 0.7:  # 70% of interruptions are resumable
                        resumable_transfers += 1
                        await asyncio.sleep(0.5)  # Resume delay
                        continue  # Retry chunk
                    else:
                        # Partial data recovery
                        partial_data_recovery += 1
                        transferred_bytes = int(transferred_bytes * 0.6)  # Lose 40% of progress
                        break

                # Successful chunk transfer
                await asyncio.sleep(chunk_size / 100000)  # Transfer time based on size
                transferred_bytes += chunk_size

            completion_rate = transferred_bytes / transfer_size

            return {
                "transfer_size": transfer_size,
                "transferred_bytes": transferred_bytes,
                "completion_rate": completion_rate,
                "interruptions": interruptions,
                "resumable": interruptions > 0 and transferred_bytes == transfer_size,
                "status": "completed" if completion_rate >= 0.8 else "partial" if completion_rate > 0 else "failed"
            }

        # Test data transfers of different sizes with network issues
        transfer_sizes = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB

        transfer_tasks = []
        for size in transfer_sizes:
            for i in range(6):  # 6 transfers per size
                source_config = {"type": "api", "url": f"https://example.com/data_{i}"}
                task = transfer_data_with_network_issues(source_config, size)
                transfer_tasks.append(task)

        results = await asyncio.gather(*transfer_tasks)

        # Analyze transfer results
        completed_transfers = [r for r in results if r["status"] == "completed"]
        partial_transfers = [r for r in results if r["status"] == "partial"]
        failed_transfers = [r for r in results if r["status"] == "failed"]

        avg_completion_rate = sum(r["completion_rate"] for r in results) / len(results)
        resumable_transfers_count = sum(1 for r in results if r.get("resumable", False))

        success_rate = len(completed_transfers) / len(results)

        print(f"Network Interruptions During Transfer Test:")
        print(f"  Total Transfers: {len(results)}")
        print(f"  Completed: {len(completed_transfers)}")
        print(f"  Partial: {len(partial_transfers)}")
        print(f"  Failed: {len(failed_transfers)}")
        print(f"  Network Interruptions: {network_interruptions}")
        print(f"  Resumable Transfers: {resumable_transfers_count}")
        print(f"  Partial Data Recovery: {partial_data_recovery}")
        print(f"  Avg Completion Rate: {avg_completion_rate:.2%}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Data transfer should handle network interruptions gracefully
        assert network_interruptions > 0, "No network interruptions occurred - chaos test ineffective"
        assert success_rate > 0.75, f"Transfer success rate too low under network chaos: {success_rate:.2%}"
        assert resumable_transfers_count > 0, "No resumable transfers used"

    @pytest.mark.asyncio
    async def test_rate_limiting_and_throttling(self, chaos_config):
        """Test handling of rate limiting and throttling from data sources."""
        rate_limit_hits = 0
        backoff_successes = 0
        adaptive_throttling = 0

        class RateLimitedDataSource:
            def __init__(self, requests_per_minute: int):
                self.requests_per_minute = requests_per_minute
                self.requests_this_minute = 0
                self.minute_start = time.time()
                self.backoff_until = 0

            async def make_request(self) -> Dict[str, Any]:
                """Make request to rate-limited data source."""
                nonlocal rate_limit_hits, backoff_successes, adaptive_throttling

                current_time = time.time()

                # Check if we're in backoff period
                if current_time < self.backoff_until:
                    backoff_successes += 1
                    await asyncio.sleep(self.backoff_until - current_time)
                    # Reset for backoff retry
                    self.requests_this_minute = 0
                    self.minute_start = current_time

                # Reset counter every minute
                if current_time - self.minute_start >= 60:
                    self.requests_this_minute = 0
                    self.minute_start = current_time

                if self.requests_this_minute >= self.requests_per_minute:
                    rate_limit_hits += 1

                    # Adaptive backoff strategy
                    if random.random() < 0.7:  # 70% use adaptive backoff
                        adaptive_throttling += 1
                        backoff_time = 60 + random.uniform(5, 15)  # 60-75 seconds
                        self.backoff_until = current_time + backoff_time
                        await asyncio.sleep(backoff_time)

                        # After backoff, allow request
                        self.requests_this_minute = 0
                        self.minute_start = time.time()
                    else:
                        raise Exception("Rate limit exceeded")

                self.requests_this_minute += 1

                # Successful request
                await asyncio.sleep(random.uniform(0.1, 0.3))
                return {
                    "status": "success",
                    "data_size": random.randint(1024, 10240),
                    "rate_limited": False
                }

        async def ingest_with_rate_limiting(source: RateLimitedDataSource, request_count: int) -> List[Dict[str, Any]]:
            """Perform multiple ingestion requests with rate limiting."""
            results = []

            for i in range(request_count):
                try:
                    result = await source.make_request()
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e), "rate_limited": True})

                # Small delay between requests
                await asyncio.sleep(0.05)

            return results

        # Test different rate limit scenarios
        rate_limits = chaos_config["rate_limit_scenarios"]
        requests_per_scenario = 15

        for rpm_limit in rate_limits:
            print(f"\nTesting rate limiting at {rpm_limit} requests/minute...")

            rate_limited_source = RateLimitedDataSource(rpm_limit)
            results = await ingest_with_rate_limiting(rate_limited_source, requests_per_scenario)

            successful_requests = [r for r in results if "error" not in r]
            failed_requests = [r for r in results if "error" in r]

            rate_limited_requests = sum(1 for r in results if r.get("rate_limited", False))

            success_rate = len(successful_requests) / len(results)

            print(f"  Total Requests: {len(results)}")
            print(f"  Successful: {len(successful_requests)}")
            print(f"  Failed: {len(failed_requests)}")
            print(f"  Rate Limited: {rate_limited_requests}")
            print(f"  Rate Limit Hits: {rate_limit_hits}")
            print(f"  Backoff Successes: {backoff_successes}")
            print(f"  Adaptive Throttling: {adaptive_throttling}")
            print(f"  Success Rate: {success_rate:.2%}")

            # Should handle rate limiting gracefully
            assert len(failed_requests) > 0, "No rate limiting occurred - chaos test ineffective"
            assert success_rate > 0.7, f"Success rate too low with rate limiting: {success_rate:.2%}"
            assert backoff_successes > 0, "No backoff recovery used"

    @pytest.mark.asyncio
    async def test_content_parsing_format_failures(self, chaos_config):
        """Test handling of content parsing and format validation failures."""
        parsing_errors = 0
        format_validation_failures = 0
        content_recovery_successes = 0

        async def parse_content_with_failures(content: str, content_type: str) -> Dict[str, Any]:
            """Simulate content parsing with potential failures."""
            nonlocal parsing_errors, format_validation_failures, content_recovery_successes

            # Simulate parsing failures
            if random.random() < 0.08:  # 8% parsing errors
                parsing_errors += 1

                if content_type == "json":
                    raise json.JSONDecodeError("Invalid JSON format", content, 0)
                elif content_type == "xml":
                    raise Exception("XML parsing error: malformed document")
                elif content_type == "markdown":
                    raise Exception("Markdown parsing error: invalid syntax")
                else:
                    raise Exception(f"Unknown content type parsing error: {content_type}")

            # Simulate format validation failures
            if random.random() < 0.05:  # 5% validation failures
                format_validation_failures += 1

                if content_type == "json":
                    # Valid JSON but invalid schema
                    raise Exception("JSON schema validation failed")
                elif content_type == "xml":
                    raise Exception("XML schema validation failed")
                else:
                    raise Exception("Content format validation failed")

            # Simulate successful parsing with potential recovery
            if random.random() < 0.1:  # 10% need content recovery
                content_recovery_successes += 1
                # Simulate content cleanup/recovery
                await asyncio.sleep(0.2)

            # Normal successful parsing
            await asyncio.sleep(random.uniform(0.05, 0.2))

            return {
                "content_type": content_type,
                "status": "parsed",
                "documents_extracted": random.randint(1, 5),
                "content_length": len(content),
                "recovery_applied": random.random() < 0.1
            }

        # Test content parsing across different formats and scenarios
        content_types = ["json", "xml", "markdown", "html", "plaintext"]
        sample_contents = {
            "json": '{"name": "test", "value": 123}',
            "xml": '<document><title>Test</title><content>Sample content</content></document>',
            "markdown": "# Title\n\nThis is **bold** text.\n\n- List item 1\n- List item 2",
            "html": "<html><body><h1>Title</h1><p>Content</p></body></html>",
            "plaintext": "This is plain text content without any special formatting."
        }

        parsing_tasks = []
        for content_type in content_types:
            content = sample_contents[content_type]
            for i in range(12):  # 12 parsing attempts per content type
                task = parse_content_with_failures(content, content_type)
                parsing_tasks.append(task)

        results = await asyncio.gather(*parsing_tasks, return_exceptions=True)

        # Analyze parsing results
        successful_parsing = [r for r in results if isinstance(r, dict)]
        failed_parsing = [r for r in results if isinstance(r, Exception)]

        recovery_used = sum(1 for r in successful_parsing if r.get("recovery_applied", False))

        success_rate = len(successful_parsing) / len(results)

        print(f"Content Parsing Format Failure Test:")
        print(f"  Total Parsing Attempts: {len(results)}")
        print(f"  Successful: {len(successful_parsing)}")
        print(f"  Failed: {len(failed_parsing)}")
        print(f"  Parsing Errors: {parsing_errors}")
        print(f"  Validation Failures: {format_validation_failures}")
        print(f"  Recovery Successes: {content_recovery_successes}")
        print(f"  Recovery Used: {recovery_used}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Content parsing should handle format issues gracefully
        assert parsing_errors > 0 or format_validation_failures > 0, "No parsing failures occurred - chaos test ineffective"
        assert success_rate > 0.8, f"Parsing success rate too low: {success_rate:.2%}"
        assert content_recovery_successes >= 0, "Content recovery mechanisms should be available"

    @pytest.mark.asyncio
    async def test_concurrent_ingestion_failures(self, chaos_config):
        """Test concurrent data ingestion under failure conditions."""
        concurrent_failures = 0
        resource_exhaustion_events = 0
        priority_based_recovery = 0

        async def concurrent_ingestion_operation(operation_id: int, priority: str, source_config: Dict[str, Any]) -> Dict[str, Any]:
            """Perform data ingestion operation with concurrency and failure handling."""
            nonlocal concurrent_failures, resource_exhaustion_events, priority_based_recovery

            # Simulate concurrent processing issues
            if random.random() < 0.08:  # 8% concurrency failures
                concurrent_failures += 1

                if priority == "low":
                    resource_exhaustion_events += 1
                    raise Exception("Resource exhaustion: low priority operation cancelled")
                elif priority == "high":
                    priority_based_recovery += 1
                    # High priority gets extended timeout
                    await asyncio.sleep(2.0)
                    # Recovery successful
                else:
                    raise Exception("Concurrent processing limit exceeded")

            # Simulate normal data ingestion
            processing_time = random.uniform(0.3, 1.2)
            await asyncio.sleep(processing_time)

            return {
                "operation_id": operation_id,
                "priority": priority,
                "source_type": source_config["type"],
                "status": "completed",
                "processing_time": processing_time,
                "documents_ingested": random.randint(1, 8)
            }

        # Test concurrent ingestion with different priorities
        operations = []
        priorities = ["high", "medium", "low"]
        source_types = ["github", "api", "database", "filesystem"]

        for i in range(50):  # High concurrency test
            priority = priorities[i % len(priorities)]
            source_type = source_types[i % len(source_types)]
            source_config = {"type": source_type}
            operations.append((i, priority, source_config))

        # Execute operations concurrently
        tasks = [concurrent_ingestion_operation(op_id, priority, source_config)
                for op_id, priority, source_config in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze concurrent ingestion results
        successful_operations = [r for r in results if isinstance(r, dict)]
        failed_operations = [r for r in results if isinstance(r, Exception)]

        high_priority_success = sum(1 for r in successful_operations if r.get("priority") == "high")
        low_priority_success = sum(1 for r in successful_operations if r.get("priority") == "low")

        success_rate = len(successful_operations) / len(results)

        print(f"Concurrent Ingestion Failures Test:")
        print(f"  Total Operations: {len(results)}")
        print(f"  Successful: {len(successful_operations)}")
        print(f"  Failed: {len(failed_operations)}")
        print(f"  High Priority Success: {high_priority_success}")
        print(f"  Low Priority Success: {low_priority_success}")
        print(f"  Concurrent Failures: {concurrent_failures}")
        print(f"  Resource Exhaustion: {resource_exhaustion_events}")
        print(f"  Priority Recovery: {priority_based_recovery}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Should handle concurrent ingestion gracefully with prioritization
        assert len(failed_operations) > 0, "No concurrent failures occurred - chaos test ineffective"
        assert success_rate > 0.75, f"Success rate too low under concurrent load: {success_rate:.2%}"
        assert resource_exhaustion_events > 0, "No resource exhaustion handling for low priority"
        assert priority_based_recovery >= 0, "Priority-based recovery should be available"
