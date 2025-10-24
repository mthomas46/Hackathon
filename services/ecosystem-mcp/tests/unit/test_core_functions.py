"""
Unit tests for core functions and utilities.

Tests individual functions in isolation to catch logic errors.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================================
# Test Circuit Breaker Logic
# ============================================================================

class TestCircuitBreaker:
    """Unit tests for circuit breaker logic."""
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes correctly."""
        from src.utils.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=5,
            timeout=60.0
        )
        
        assert breaker.name == "test"
        assert breaker.config.failure_threshold == 5
        assert breaker.config.timeout == 60.0
        assert breaker.stats.failure_count == 0
    
    def test_circuit_breaker_state_transitions(self):
        """Test circuit breaker state transitions via context manager."""
        from src.utils.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenError
        import asyncio
        
        breaker = CircuitBreaker(name="test", failure_threshold=2)
        
        # Should start CLOSED
        assert breaker.stats.state == CircuitState.CLOSED
        
        # Simulate failures by calling the circuit breaker and raising exceptions
        async def failing_operation():
            async with breaker:
                raise Exception("Simulated failure")
        
        # Record first failure
        try:
            asyncio.run(failing_operation())
        except Exception:
            pass
        
        assert breaker.stats.state == CircuitState.CLOSED  # Still closed after 1 failure
        
        # Record second failure
        try:
            asyncio.run(failing_operation())
        except Exception:
            pass
        
        assert breaker.stats.state == CircuitState.OPEN  # Should open after threshold


# ============================================================================
# Test Worker ID Generation
# ============================================================================

class TestWorkerIDGeneration:
    """Test worker ID generation logic."""
    
    def test_worker_id_is_unique(self):
        """Test that worker IDs are unique when creating new instances."""
        from src.services.ingestion.ingestion_worker import IngestionWorker
        
        # Create two separate instances (not using singleton)
        worker1 = IngestionWorker()
        worker2 = IngestionWorker()
        
        assert worker1.worker_id != worker2.worker_id
    
    def test_worker_id_format(self):
        """Test worker ID has expected format."""
        from src.services.ingestion import get_ingestion_worker
        
        worker = get_ingestion_worker()
        
        # Should be 8 characters (truncated UUID)
        assert len(worker.worker_id) == 8
        # Should be alphanumeric
        assert worker.worker_id.replace('-', '').isalnum()


# ============================================================================
# Test Normalizer Factory
# ============================================================================

class TestNormalizerFactory:
    """Unit tests for normalizer factory."""
    
    def test_normalizer_factory_markdown(self):
        """Test factory returns markdown normalizer for .md files."""
        from src.services.processing import NormalizerFactory
        
        factory = NormalizerFactory()
        normalizer = factory.get_normalizer(".md")
        
        assert normalizer is not None
        assert hasattr(normalizer, 'normalize')
    
    def test_normalizer_factory_python(self):
        """Test factory returns python normalizer for .py files."""
        from src.services.processing import NormalizerFactory
        
        factory = NormalizerFactory()
        normalizer = factory.get_normalizer(".py")
        
        assert normalizer is not None
        assert hasattr(normalizer, 'normalize')
    
    def test_normalizer_factory_unknown(self):
        """Test factory handles unknown file types."""
        from src.services.processing import NormalizerFactory
        
        factory = NormalizerFactory()
        normalizer = factory.get_normalizer(".xyz")
        
        # Should return text normalizer as fallback
        assert normalizer is not None


# ============================================================================
# Test Cache Key Generation
# ============================================================================

class TestCacheKeyGeneration:
    """Test cache key generation logic."""
    
    def test_cache_key_uniqueness(self):
        """Test that different inputs generate different cache keys."""
        import hashlib
        import json
        
        # Simulate cache key generation
        def generate_cache_key(prefix: str, *args, **kwargs):
            key_data = json.dumps([args, sorted(kwargs.items())])
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        
        key1 = generate_cache_key("search", "test query", limit=10)
        key2 = generate_cache_key("search", "different query", limit=10)
        key3 = generate_cache_key("search", "test query", limit=20)
        
        assert key1 != key2  # Different query
        assert key1 != key3  # Different limit
        assert key2 != key3  # Different everything


# ============================================================================
# Test Repository Base Operations
# ============================================================================

class TestRepositoryBase:
    """Unit tests for base repository operations."""
    
    @pytest.mark.asyncio
    async def test_repository_init_parameter_order(self):
        """Test repository initialization with correct parameter order."""
        from src.storage.repositories import DocumentRepository
        from unittest.mock import MagicMock
        
        # Mock session
        mock_session = MagicMock()
        
        # Should not raise error
        repo = DocumentRepository(mock_session)
        
        assert repo.session == mock_session
        assert hasattr(repo, 'model_class')


# ============================================================================
# Test Git Service Methods
# ============================================================================

class TestGitServiceMethods:
    """Unit tests for Git service method aliases."""
    
    @pytest.mark.asyncio
    async def test_get_recent_commits_alias(self):
        """Test get_recent_commits is properly aliased."""
        from src.services.git import GitService
        
        git_service = GitService("/Users/mykalthomas/Documents/work/Hackathon")
        
        # Verify method exists
        assert hasattr(git_service, 'get_recent_commits')
        assert callable(git_service.get_recent_commits)
    
    @pytest.mark.asyncio
    async def test_get_commit_files_alias(self):
        """Test get_commit_files is properly aliased."""
        from src.services.git import GitService
        
        git_service = GitService("/Users/mykalthomas/Documents/work/Hackathon")
        
        # Verify method exists
        assert hasattr(git_service, 'get_commit_files')
        assert callable(git_service.get_commit_files)


# ============================================================================
# Test Redis Stream Constants
# ============================================================================

class TestRedisStreamConstants:
    """Test Redis stream constants are defined."""
    
    def test_redis_stream_constants_exist(self):
        """Test that all required stream constants exist."""
        from src.utils.redis_client import RedisClient
        
        redis = RedisClient()
        
        assert hasattr(redis, 'INGESTION_STREAM')
        assert hasattr(redis, 'EMBEDDING_STREAM')
        assert hasattr(redis, 'FAILED_STREAM')
        assert hasattr(redis, 'CONSUMER_GROUP')
        
        # Verify they're strings
        assert isinstance(redis.INGESTION_STREAM, str)
        assert isinstance(redis.CONSUMER_GROUP, str)


# ============================================================================
# Test Ollama Client Configuration
# ============================================================================

class TestOllamaClientConfiguration:
    """Test Ollama client configuration."""
    
    def test_ollama_client_has_circuit_breaker(self):
        """Test Ollama client initializes with circuit breaker."""
        from src.services.models.ollama_client import OllamaClient
        
        client = OllamaClient()
        
        assert hasattr(client, 'circuit_breaker'), "Client must have circuit_breaker"
        assert hasattr(client.circuit_breaker, 'stats'), "Circuit breaker must have stats"
        assert hasattr(client.circuit_breaker.stats, 'state'), "Circuit breaker stats must have state"
        assert hasattr(client.circuit_breaker, 'get_state'), "Circuit breaker must have get_state method"
        # Circuit breaker uses context manager, not direct record methods
    
    def test_ollama_client_base_url_configuration(self):
        """Test Ollama client uses correct base URL."""
        from src.services.models.ollama_client import OllamaClient
        from src.config import settings
        
        client = OllamaClient()
        
        assert client.base_url == settings.ollama_base_url
        assert client.base_url.startswith("http")


# ============================================================================
# Test Embedding Service Configuration
# ============================================================================

class TestEmbeddingServiceConfiguration:
    """Test embedding service configuration."""
    
    def test_embedding_service_singleton(self):
        """Test embedding service returns singleton."""
        from src.services.embeddings import get_embedding_service
        
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        
        # Should be same instance
        assert service1 is service2
    
    def test_embedding_service_has_ollama_client(self):
        """Test embedding service has Ollama client."""
        from src.services.embeddings import get_embedding_service
        
        service = get_embedding_service()
        
        assert hasattr(service, 'ollama_client')
        assert service.ollama_client is not None


# ============================================================================
# Test Document Model Fields
# ============================================================================

class TestDocumentModelFields:
    """Test DocumentModel has correct fields."""
    
    def test_document_model_required_fields(self):
        """Test DocumentModel has all required fields."""
        from src.storage.db_models import DocumentModel
        
        # Get all column names
        columns = [col.name for col in DocumentModel.__table__.columns]
        
        # Check required fields exist
        required_fields = [
            'id', 'service_name', 'file_path', 'original_format',
            'original_content', 'normalized_content', 'content_hash',
            'doc_metadata'
        ]
        
        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"


# ============================================================================
# Run Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

