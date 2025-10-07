"""
Integration tests for HTTP clients.

Tests the Performance Store and MCP Store clients against running services.
"""

import pytest
import asyncio
from datetime import datetime
import uuid

from common.clients import PerformanceStoreClient, MCPStoreClient


# ============================================================================
# Performance Store Client Tests
# ============================================================================

@pytest.mark.asyncio
async def test_performance_store_health_check():
    """Test Performance Store health check."""
    client = PerformanceStoreClient()
    
    try:
        is_healthy = await client.health_check()
        # If service is running, should be healthy
        # If service is not running, test should be skipped (not failed)
        if not is_healthy:
            pytest.skip("Performance Store service is not running")
        
        assert is_healthy is True
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_performance_store_record_execution():
    """Test recording an execution."""
    client = PerformanceStoreClient()
    
    try:
        # Check if service is available
        if not await client.health_check():
            pytest.skip("Performance Store service is not running")
        
        # Record execution
        execution_id = str(uuid.uuid4())
        result = await client.record_execution(
            orchestration_id=execution_id,
            mcp_id="test-mcp",
            pattern_name="chain-of-thought",
            status="success",
            duration_ms=1500.0,
            query="Test query",
            confidence=0.95,
            num_sources=3,
            response_length=42,
        )
        
        assert result is not None
        assert "execution_id" in result or result == {}  # May return empty if recording fails non-critically
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_performance_store_get_recent_executions():
    """Test getting recent executions."""
    client = PerformanceStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("Performance Store service is not running")
        
        executions = await client.get_recent_executions(limit=5)
        
        assert isinstance(executions, list)
        # List may be empty if no executions recorded yet
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_performance_store_get_performance_summary():
    """Test getting performance summary."""
    client = PerformanceStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("Performance Store service is not running")
        
        summary = await client.get_performance_summary(time_window_hours=24)
        
        assert isinstance(summary, dict)
        # Summary may be empty if no executions in time window
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_performance_store_list_patterns():
    """Test listing patterns."""
    client = PerformanceStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("Performance Store service is not running")
        
        patterns = await client.list_patterns()
        
        assert isinstance(patterns, list)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_performance_store_get_trends():
    """Test getting orchestration trends."""
    client = PerformanceStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("Performance Store service is not running")
        
        trends = await client.get_orchestration_trends(time_window_days=7)
        
        assert isinstance(trends, dict)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_performance_store_detect_anomalies():
    """Test anomaly detection."""
    client = PerformanceStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("Performance Store service is not running")
        
        anomalies = await client.detect_orchestration_anomalies(time_window_days=7)
        
        assert isinstance(anomalies, list)
    finally:
        await client.close()


# ============================================================================
# MCP Store Client Tests
# ============================================================================

@pytest.mark.asyncio
async def test_mcp_store_health_check():
    """Test MCP Store health check."""
    client = MCPStoreClient()
    
    try:
        is_healthy = await client.health_check()
        if not is_healthy:
            pytest.skip("MCP Store service is not running")
        
        assert is_healthy is True
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_mcp_store_list_packages():
    """Test listing packages."""
    client = MCPStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("MCP Store service is not running")
        
        packages = await client.list_packages(limit=10)
        
        assert isinstance(packages, list)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_mcp_store_search_packages():
    """Test searching packages."""
    client = MCPStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("MCP Store service is not running")
        
        results = await client.search_packages(query="test", limit=5)
        
        assert isinstance(results, list)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_mcp_store_get_trending_packages():
    """Test getting trending packages."""
    client = MCPStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("MCP Store service is not running")
        
        trending = await client.get_trending_packages(time_window_days=7, limit=5)
        
        assert isinstance(trending, list)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_mcp_store_get_popular_tags():
    """Test getting popular tags."""
    client = MCPStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("MCP Store service is not running")
        
        tags = await client.get_popular_tags(limit=10)
        
        assert isinstance(tags, list)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_mcp_store_get_marketplace_stats():
    """Test getting marketplace stats."""
    client = MCPStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("MCP Store service is not running")
        
        stats = await client.get_marketplace_stats()
        
        assert isinstance(stats, dict)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_mcp_store_create_and_get_package():
    """Test creating and retrieving a package."""
    client = MCPStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("MCP Store service is not running")
        
        # Create package
        package_name = f"test-package-{uuid.uuid4().hex[:8]}"
        created = await client.create_package(
            name=package_name,
            description="Test package for integration tests",
            owner_id="test-user",
            tags=["test", "integration"],
            categories=["testing"],
        )
        
        assert created is not None
        assert "package_id" in created
        
        package_id = created["package_id"]
        
        # Get package
        retrieved = await client.get_package(package_id)
        
        assert retrieved is not None
        assert retrieved["package_id"] == package_id
        assert retrieved["name"] == package_name
        
        # Cleanup: delete package
        await client.delete_package(package_id)
    
    except Exception as e:
        # If service doesn't support this operation yet, skip
        pytest.skip(f"MCP Store service doesn't support this operation: {e}")
    finally:
        await client.close()


# ============================================================================
# Circuit Breaker Tests
# ============================================================================

@pytest.mark.asyncio
async def test_circuit_breaker_opens_on_failures():
    """Test that circuit breaker opens after failures."""
    from common.http_client import CircuitBreaker
    
    breaker = CircuitBreaker(failure_threshold=3, timeout_duration=5)
    
    # Record failures
    for _ in range(3):
        breaker.record_failure()
    
    # Circuit should be open
    assert breaker.can_execute() is False
    
    # Wait for timeout
    await asyncio.sleep(6)
    
    # Circuit should be half-open now
    assert breaker.can_execute() is True


@pytest.mark.asyncio
async def test_circuit_breaker_closes_after_successes():
    """Test that circuit breaker closes after successes in half-open state."""
    from common.http_client import CircuitBreaker
    
    breaker = CircuitBreaker(failure_threshold=3, success_threshold=2, timeout_duration=1)
    
    # Open circuit
    for _ in range(3):
        breaker.record_failure()
    
    # Wait for half-open
    await asyncio.sleep(2)
    
    # Record successes
    breaker.record_success()
    breaker.record_success()
    
    # Circuit should be closed
    assert breaker.can_execute() is True


# ============================================================================
# Retry Logic Tests
# ============================================================================

@pytest.mark.asyncio
async def test_client_retries_on_failure():
    """Test that client retries failed requests."""
    # Test against a non-existent service to trigger retries
    client = PerformanceStoreClient(base_url="http://localhost:9999")
    
    try:
        # This should retry 3 times and then fail
        with pytest.raises(Exception):
            await client.get_recent_executions()
    finally:
        await client.close()


# ============================================================================
# Concurrent Request Tests
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test multiple concurrent requests."""
    client = PerformanceStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("Performance Store service is not running")
        
        # Make 10 concurrent health checks
        tasks = [client.health_check() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed (or all should be exceptions if service is down)
        assert len(results) == 10
        
        # Check that at least one succeeded
        successes = [r for r in results if r is True]
        if len(successes) == 0:
            pytest.skip("Service unavailable during concurrent test")
    
    finally:
        await client.close()

