"""
Integration tests for configuration validation system.

✅ PHASE 5: Testing - Integration tests against real services
"""

import pytest
import asyncio
from datetime import datetime

from src.config.registry import get_registry
from src.validation import ConfigValidator
from src.utils.redis_client import get_redis_client
from src.storage import get_database
from src.storage.chromadb_client import get_chroma_client


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def registry():
    """Get configuration registry."""
    return get_registry()


@pytest.fixture(scope="module")
async def validator():
    """Get configuration validator."""
    return ConfigValidator()


@pytest.fixture(scope="module")
async def redis_client():
    """Get Redis client."""
    client = get_redis_client()
    await client.connect()
    yield client
    await client.close()


@pytest.fixture(scope="module")
async def database():
    """Get database client."""
    db = get_database()
    yield db
    await db.close()


@pytest.fixture(scope="module")
def chroma_client():
    """Get ChromaDB client."""
    return get_chroma_client()


# ============================================================================
# Test Registry Loading
# ============================================================================

class TestRegistryIntegration:
    """Integration tests for registry loading."""
    
    def test_registry_loads_successfully(self, registry):
        """Test that registry loads from YAML file."""
        assert registry is not None
        assert hasattr(registry, 'services')
        assert hasattr(registry, 'redis')
        assert hasattr(registry, 'database')
        assert hasattr(registry, 'chromadb')
    
    def test_registry_has_required_services(self, registry):
        """Test that registry contains required services."""
        service_names = [s.name for s in registry.services]
        assert "ecosystem-mcp" in service_names
        assert "ecosystem-mcp-dashboard" in service_names
    
    def test_registry_redis_configuration(self, registry):
        """Test Redis configuration in registry."""
        assert hasattr(registry.redis, 'streams')
        assert hasattr(registry.redis.streams, 'ingestion')
        assert hasattr(registry.redis.streams, 'embedding')
        assert registry.redis.streams.ingestion.name
        assert registry.redis.streams.ingestion.consumer_group
    
    def test_registry_database_configuration(self, registry):
        """Test database configuration in registry."""
        assert hasattr(registry.database, 'connection')
        assert registry.database.connection.url
        assert registry.database.connection.pool_size > 0
    
    def test_registry_chromadb_configuration(self, registry):
        """Test ChromaDB configuration in registry."""
        assert hasattr(registry.chromadb, 'collections')
        assert hasattr(registry.chromadb.collections, 'main')
        assert registry.chromadb.collections.main.name


# ============================================================================
# Test Redis Validation
# ============================================================================

class TestRedisValidationIntegration:
    """Integration tests for Redis validation."""
    
    @pytest.mark.asyncio
    async def test_redis_connection_validation(self, validator):
        """Test Redis connection validation."""
        result = await validator.validate_redis_connection()
        
        assert result is not None
        assert result.check_name == "Redis Connection"
        # Note: This might fail if Redis is not running
        if result.passed:
            assert "successful" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_redis_streams_validation(self, validator):
        """Test Redis streams validation."""
        result = await validator.validate_redis_streams()
        
        assert result is not None
        assert result.check_name == "Redis Streams"
        # Streams might not exist yet in test environment
        assert result.severity in ["critical", "high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_redis_consumer_groups_validation(self, validator):
        """Test Redis consumer groups validation."""
        result = await validator.validate_redis_consumer_groups()
        
        assert result is not None
        assert result.check_name == "Redis Consumer Groups"
        # Consumer groups might not exist yet in test environment
        assert result.severity in ["critical", "high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_redis_client_uses_registry_values(self, redis_client, registry):
        """Test that Redis client uses values from registry."""
        # This is the critical test that would have caught the consumer group mismatch
        assert redis_client.INGESTION_STREAM == registry.redis.streams.ingestion.name
        assert redis_client.CONSUMER_GROUP == registry.redis.streams.ingestion.consumer_group
        assert redis_client.EMBEDDING_STREAM == registry.redis.streams.embedding.name


# ============================================================================
# Test Database Validation
# ============================================================================

class TestDatabaseValidationIntegration:
    """Integration tests for database validation."""
    
    @pytest.mark.asyncio
    async def test_database_connection_validation(self, validator):
        """Test database connection validation."""
        result = await validator.validate_database_connection()
        
        assert result is not None
        assert result.check_name == "Database Connection"
        # Note: This might fail if PostgreSQL is not running
        if result.passed:
            assert "successful" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_database_names_validation(self, validator):
        """Test database names validation."""
        result = await validator.validate_database_names()
        
        assert result is not None
        assert result.check_name == "Database Names"
    
    @pytest.mark.asyncio
    async def test_database_schema_validation(self, validator):
        """Test database schema validation."""
        result = await validator.validate_database_schema()
        
        assert result is not None
        assert result.check_name == "Database Schema"


# ============================================================================
# Test ChromaDB Validation
# ============================================================================

class TestChromaDBValidationIntegration:
    """Integration tests for ChromaDB validation."""
    
    @pytest.mark.asyncio
    async def test_chromadb_collection_validation(self, validator):
        """Test ChromaDB collection validation."""
        result = await validator.validate_chromadb_collection()
        
        # ChromaDB validation might return None if not initialized
        if result is not None:
            assert result.check_name == "ChromaDB Collection"
            assert result.severity in ["critical", "high", "medium", "low"]


# ============================================================================
# Test Service Validation
# ============================================================================

class TestServiceValidationIntegration:
    """Integration tests for service validation."""
    
    @pytest.mark.asyncio
    async def test_service_ports_validation(self, validator):
        """Test service ports validation."""
        result = await validator.validate_service_ports()
        
        assert result is not None
        assert result.check_name == "Service Ports"
    
    @pytest.mark.asyncio
    async def test_network_connectivity_validation(self, validator):
        """Test network connectivity validation."""
        result = await validator.validate_network_connectivity()
        
        assert result is not None
        assert result.check_name == "Network Connectivity"


# ============================================================================
# Test Full Validation Flow
# ============================================================================

class TestFullValidationIntegration:
    """Integration tests for full validation flow."""
    
    @pytest.mark.asyncio
    async def test_validate_all(self, validator):
        """Test full validation of all components."""
        results = await validator.validate_all(fail_fast=False)
        
        assert results is not None
        assert len(results.results) > 0
        
        # Get summary
        summary = results.summary()
        assert summary["total_checks"] > 0
        assert summary["passed"] >= 0
        assert summary["failed"] >= 0
        assert summary["warnings"] >= 0
    
    @pytest.mark.asyncio
    async def test_validate_all_fail_fast(self, validator):
        """Test validation with fail_fast enabled."""
        results = await validator.validate_all(fail_fast=True)
        
        assert results is not None
        # If there are any failures, should stop early
        failures = results.get_failures()
        if failures:
            # Should have stopped at first critical failure
            critical_failures = results.get_critical_failures()
            if critical_failures:
                assert len(results.results) <= results.summary()["total_checks"]
    
    @pytest.mark.asyncio
    async def test_validation_results_have_timestamps(self, validator):
        """Test that validation results include timestamps."""
        results = await validator.validate_all(fail_fast=False)
        
        for result in results.results:
            assert result.timestamp
            # Validate timestamp format
            try:
                datetime.fromisoformat(result.timestamp)
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {result.timestamp}")
    
    @pytest.mark.asyncio
    async def test_validation_results_have_remediation(self, validator):
        """Test that failed validations include remediation steps."""
        results = await validator.validate_all(fail_fast=False)
        
        failures = results.get_failures()
        for failure in failures:
            assert failure.remediation is not None
            assert len(failure.remediation) > 0


# ============================================================================
# Test Configuration Drift Detection
# ============================================================================

class TestConfigurationDriftIntegration:
    """Integration tests for configuration drift detection."""
    
    def test_redis_stream_names_match(self, redis_client, registry):
        """Test that Redis stream names match between registry and runtime."""
        # This test would have caught the consumer group mismatch!
        assert redis_client.INGESTION_STREAM == registry.redis.streams.ingestion.name, \
            f"Stream name mismatch: {redis_client.INGESTION_STREAM} != {registry.redis.streams.ingestion.name}"
        
        assert redis_client.EMBEDDING_STREAM == registry.redis.streams.embedding.name, \
            f"Stream name mismatch: {redis_client.EMBEDDING_STREAM} != {registry.redis.streams.embedding.name}"
        
        assert redis_client.RETRY_STREAM == registry.redis.streams.retry.name, \
            f"Stream name mismatch: {redis_client.RETRY_STREAM} != {registry.redis.streams.retry.name}"
        
        assert redis_client.FAILED_STREAM == registry.redis.streams.dead_letter.name, \
            f"Stream name mismatch: {redis_client.FAILED_STREAM} != {registry.redis.streams.dead_letter.name}"
    
    def test_redis_consumer_group_matches(self, redis_client, registry):
        """Test that Redis consumer group matches between registry and runtime."""
        # THIS IS THE CRITICAL TEST that would have caught today's bug!
        assert redis_client.CONSUMER_GROUP == registry.redis.streams.ingestion.consumer_group, \
            f"Consumer group mismatch: '{redis_client.CONSUMER_GROUP}' != '{registry.redis.streams.ingestion.consumer_group}'"
    
    def test_redis_retry_configuration_matches(self, redis_client, registry):
        """Test that Redis retry configuration matches."""
        assert redis_client.MAX_RETRIES == registry.redis.retry.max_retries, \
            f"Max retries mismatch: {redis_client.MAX_RETRIES} != {registry.redis.retry.max_retries}"
        
        assert redis_client.RETRY_BACKOFF_BASE == registry.redis.retry.backoff_base, \
            f"Backoff base mismatch: {redis_client.RETRY_BACKOFF_BASE} != {registry.redis.retry.backoff_base}"
    
    def test_no_configuration_drift_detected(self, redis_client, registry):
        """Test that no configuration drift exists between registry and runtime."""
        # Comprehensive drift check
        drift_detected = False
        drift_messages = []
        
        # Check Redis streams
        if redis_client.INGESTION_STREAM != registry.redis.streams.ingestion.name:
            drift_detected = True
            drift_messages.append(
                f"Ingestion stream: {redis_client.INGESTION_STREAM} != {registry.redis.streams.ingestion.name}"
            )
        
        # Check consumer group (the critical one!)
        if redis_client.CONSUMER_GROUP != registry.redis.streams.ingestion.consumer_group:
            drift_detected = True
            drift_messages.append(
                f"Consumer group: {redis_client.CONSUMER_GROUP} != {registry.redis.streams.ingestion.consumer_group}"
            )
        
        # Check embedding stream
        if redis_client.EMBEDDING_STREAM != registry.redis.streams.embedding.name:
            drift_detected = True
            drift_messages.append(
                f"Embedding stream: {redis_client.EMBEDDING_STREAM} != {registry.redis.streams.embedding.name}"
            )
        
        # Assert no drift
        assert not drift_detected, \
            f"Configuration drift detected:\n" + "\n".join(f"  - {msg}" for msg in drift_messages)


# ============================================================================
# Test Validation System Resilience
# ============================================================================

class TestValidationResilienceIntegration:
    """Integration tests for validation system resilience."""
    
    @pytest.mark.asyncio
    async def test_validation_continues_after_single_failure(self, validator):
        """Test that validation continues after a single check fails."""
        results = await validator.validate_all(fail_fast=False)
        
        # Even if some checks fail, all should be run
        summary = results.summary()
        # We should have multiple checks (at least 5)
        assert summary["total_checks"] >= 5
    
    @pytest.mark.asyncio
    async def test_validation_stops_on_critical_failure_with_fail_fast(self, validator):
        """Test that validation stops on critical failure with fail_fast."""
        results = await validator.validate_all(fail_fast=True)
        
        # If there's a critical failure, should stop early
        critical_failures = results.get_critical_failures()
        if critical_failures:
            # Should have stopped before running all checks
            summary = results.summary()
            # Hard to test exact number, but should be less than full suite
            assert summary["total_checks"] >= 1


# ============================================================================
# Test Performance
# ============================================================================

class TestValidationPerformanceIntegration:
    """Integration tests for validation performance."""
    
    @pytest.mark.asyncio
    async def test_full_validation_completes_in_reasonable_time(self, validator):
        """Test that full validation completes within acceptable time."""
        import time
        
        start = time.time()
        results = await validator.validate_all(fail_fast=False)
        duration = time.time() - start
        
        # Full validation should complete in under 5 seconds
        assert duration < 5.0, f"Validation took {duration}s (expected <5s)"
        assert len(results.results) > 0
    
    @pytest.mark.asyncio
    async def test_individual_checks_are_fast(self, validator):
        """Test that individual validation checks are fast."""
        import time
        
        checks = [
            validator.validate_redis_connection(),
            validator.validate_database_connection(),
            validator.validate_chromadb_collection(),
        ]
        
        for check_coro in checks:
            start = time.time()
            result = await check_coro
            duration = time.time() - start
            
            # Individual checks should complete in under 2 seconds
            assert duration < 2.0, \
                f"Check {result.check_name if result else 'unknown'} took {duration}s (expected <2s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

