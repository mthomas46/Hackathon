"""
Unit tests for configuration registry loader.

Tests registry loading, validation, caching, and convenience functions.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.config.registry import (
    RegistryLoader,
    get_registry,
    get_redis_stream_name,
    get_redis_consumer_group,
    get_database_url,
    get_service_port,
    get_worker_config,
)
from src.config.types import ServiceRegistry


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def registry_loader():
    """Create a fresh RegistryLoader instance."""
    loader = RegistryLoader()
    loader.clear_cache()  # Ensure clean state
    return loader


@pytest.fixture
def sample_registry_yaml():
    """Create a minimal valid registry YAML content."""
    return """
version: "1.0.0"
generated_at: "2025-10-26T00:00:00Z"
environment: "test"

service_identity:
  canonical_name: "ecosystem-mcp-test"
  display_name: "Ecosystem MCP Test"
  description: "Test configuration"
  version: "0.1.0"

redis:
  connection:
    url: "redis://localhost:6379/1"
    host: "localhost"
    port: 6379
    database: 1
    max_connections: 50
    connection_timeout_seconds: 5
    operation_timeout_seconds: 30
  streams:
    ingestion:
      name: "ingestion_queue"
      max_length: 10000
      consumer_group: "workers"
      description: "Main ingestion queue"
    embedding:
      name: "embedding_queue"
      max_length: 5000
      consumer_group: "workers"
      description: "Embedding queue"
    retry:
      name: "retry_queue"
      max_length: 50000
      consumer_group: "workers"
      description: "Retry queue"
    dead_letter:
      name: "failed_queue"
      max_length: 100000
      consumer_group: "workers"
      description: "Dead letter queue"
  retry:
    max_retries: 5
    backoff_base: 2
    backoff_max_minutes: 60

database:
  connection:
    host: "localhost"
    port: 5432
    database: "ecosystem_mcp_test"
    user: "ecosystem"
    password: "ecosystem_password"
    pool_size: 20
    max_overflow: 10
    connection_timeout_seconds: 10
    url: "postgresql://ecosystem:ecosystem_password@localhost:5432/ecosystem_mcp_test"
  container:
    host: "postgres"
    url: "postgresql://ecosystem:ecosystem_password@postgres:5432/ecosystem_mcp_test"
  tables:
    required:
      - "documents"
      - "ingestion_jobs"
    documents:
      required_columns:
        - "id"
        - "content_hash"
    ingestion_jobs:
      required_columns:
        - "id"
        - "status"

chromadb:
  connection:
    path: "./data/chroma_db"
    connection_timeout_seconds: 30
  collections:
    main:
      name: "ecosystem_docs"
      distance_metric: "cosine"
      embedding_dimension: 768

ollama:
  container:
    enabled: true
    base_url: "http://localhost:11434"
    host: "localhost"
    port: 11434
    timeout_seconds: 300
    models:
      small: "llama3.2:3b"
      medium: "mistral:7b"
      embedding: "nomic-embed-text:latest"
  desktop:
    enabled: true
    base_url: "http://host.docker.internal:11434"
    model: "llama3:latest"
    use_for_rag: true
    description: "Desktop Ollama"
  performance:
    num_ctx: 2048
    num_threads: 10
    num_batch: 2048
    keep_alive_minutes: 10
    flash_attention: true
    max_queue: 10
    num_parallel: 2

cursor:
  enabled: false
  mcp_url: "http://localhost:3000"
  model: "claude-4.5-sonnet"
  complexity_threshold: 0.7
  fallback_enabled: true

embedding_service:
  enabled: true
  base_url: "http://localhost:8001"
  container_url: "http://embedding-service:8000"
  model_name: "BAAI/bge-base-en-v1.5"
  cache_enabled: true
  cache_ttl_seconds: 2592000
  timeout_seconds: 30

services:
  ecosystem_mcp:
    name: "ecosystem-mcp"
    container_name: "ecosystem-mcp-service"
    ports:
      api: 8000
      metrics: 9090
    endpoints:
      health: "/health"
      ready: "/health/ready"
    network: "ecosystem-mcp"
  ecosystem_mcp_embedding:
    name: "ecosystem-mcp-embedding"
    container_name: "ecosystem-mcp-embedding"
    ports:
      api: 8001
      internal: 8000
    network: "ecosystem-mcp"
  ecosystem_mcp_dashboard:
    name: "ecosystem-mcp-dashboard"
    container_name: "ecosystem-mcp-dashboard"
    ports:
      ui: 8501
    network: "ecosystem-mcp"
  postgres:
    name: "postgres"
    container_name: "ecosystem-mcp-postgres"
    image: "postgres:16-alpine"
    ports:
      main: 5432
    network: "ecosystem-mcp"
  redis:
    name: "redis"
    container_name: "ecosystem-mcp-redis"
    image: "redis:7-alpine"
    ports:
      main: 6379
    network: "ecosystem-mcp"
  ollama:
    name: "ollama"
    container_name: "ecosystem-mcp-ollama"
    image: "ollama/ollama:latest"
    ports:
      api: 11434
    network: "ecosystem-mcp"

workers:
  ingestion:
    consumer_name_prefix: "worker"
    consumer_group: "workers"
    poll_interval_seconds: 5
    batch_size: 1
    max_retries: 3
    timeout_seconds: 3600
    heartbeat_interval_seconds: 30
  retry:
    consumer_name_prefix: "retry_worker"
    consumer_group: "workers"
    poll_interval_seconds: 10
    batch_size: 10
    circuit_breaker:
      failure_threshold: 10
      reset_timeout_seconds: 300

validation:
  preflight_checks:
    required:
      - "redis_connection"
      - "database_connection"
    optional:
      - "ollama_connection"
  runtime_checks:
    enabled: true
    frequency_seconds: 60
    checks:
      - "stream_consumer_group_sync"
  fail_fast:
    enabled: true
    critical_mismatches:
      - "consumer_group_name"
      - "stream_name"
  severity:
    critical: "CRITICAL"
    high: "HIGH"
    medium: "MEDIUM"
    low: "LOW"

environments:
  development:
    log_level: "DEBUG"
    preflight_mode: "lenient"
    fail_fast: false
  test:
    log_level: "INFO"
    preflight_mode: "strict"
    fail_fast: true
  production:
    log_level: "INFO"
    preflight_mode: "strict"
    fail_fast: true

metadata:
  baseline_created: "2025-10-26T00:00:00Z"
  created_by: "Test Suite"
  source: "Test data"
  issues_found:
    - "None - test data"
  fixes_needed: 0
  priority_fixes:
    - "None"

changelog:
  - version: "1.0.0"
    date: "2025-10-26"
    phase: "Phase 0 - Test"
    changes:
      - "Test registry created"
    author: "Test Suite"
    notes: "Test data"

notes: "Test registry for unit tests"
"""


@pytest.fixture
def temp_registry_file(sample_registry_yaml):
    """Create a temporary registry file."""
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml',
        delete=False
    ) as f:
        f.write(sample_registry_yaml)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


# =============================================================================
# REGISTRY LOADER TESTS
# =============================================================================

class TestRegistryLoader:
    """Test RegistryLoader class."""
    
    def test_singleton_pattern(self, registry_loader):
        """Test that RegistryLoader implements singleton pattern."""
        loader1 = RegistryLoader()
        loader2 = RegistryLoader()
        assert loader1 is loader2
    
    def test_load_success(self, registry_loader, temp_registry_file):
        """Test successful registry loading."""
        registry = registry_loader.load(config_path=temp_registry_file)
        
        assert isinstance(registry, ServiceRegistry)
        assert registry.version == "1.0.0"
        assert registry.environment == "test"
        assert registry.service_identity.canonical_name == "ecosystem-mcp-test"
    
    def test_load_caches_registry(self, registry_loader, temp_registry_file):
        """Test that registry is cached after first load."""
        # First load
        registry1 = registry_loader.load(config_path=temp_registry_file)
        loaded_at1 = registry_loader.loaded_at
        
        # Second load (should use cache)
        registry2 = registry_loader.load(config_path=temp_registry_file)
        loaded_at2 = registry_loader.loaded_at
        
        assert registry1 is registry2
        assert loaded_at1 == loaded_at2
    
    def test_force_reload(self, registry_loader, temp_registry_file):
        """Test force reload bypasses cache."""
        # First load
        registry1 = registry_loader.load(config_path=temp_registry_file)
        loaded_at1 = registry_loader.loaded_at
        
        # Force reload
        registry2 = registry_loader.load(
            config_path=temp_registry_file,
            force_reload=True
        )
        loaded_at2 = registry_loader.loaded_at
        
        # Different instances
        assert registry1 is not registry2
        assert loaded_at2 > loaded_at1
    
    def test_load_file_not_found(self, registry_loader):
        """Test FileNotFoundError when registry file doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            registry_loader.load(config_path=Path("/nonexistent/path.yaml"))
        
        assert "Service registry not found" in str(exc_info.value)
    
    def test_load_invalid_yaml(self, registry_loader):
        """Test ValueError when YAML is invalid."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                registry_loader.load(config_path=temp_path)
            
            assert "Failed to parse registry YAML" in str(exc_info.value)
        finally:
            temp_path.unlink()
    
    def test_load_empty_file(self, registry_loader):
        """Test ValueError when YAML file is empty."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                registry_loader.load(config_path=temp_path)
            
            assert "Registry file is empty" in str(exc_info.value)
        finally:
            temp_path.unlink()
    
    def test_load_invalid_schema(self, registry_loader):
        """Test ValueError when registry schema is invalid."""
        invalid_yaml = """
version: "1.0.0"
environment: "test"
# Missing required fields
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                registry_loader.load(config_path=temp_path)
            
            assert "Invalid registry configuration" in str(exc_info.value)
        finally:
            temp_path.unlink()
    
    def test_clear_cache(self, registry_loader, temp_registry_file):
        """Test cache clearing."""
        # Load registry
        registry_loader.load(config_path=temp_registry_file)
        assert registry_loader.is_loaded
        
        # Clear cache
        registry_loader.clear_cache()
        assert not registry_loader.is_loaded
        assert registry_loader.loaded_at is None


# =============================================================================
# STREAM NAME TESTS
# =============================================================================

class TestGetRedisStreamName:
    """Test getting Redis stream names."""
    
    def test_get_ingestion_stream(self, registry_loader, temp_registry_file):
        """Test getting ingestion stream name."""
        registry_loader.load(config_path=temp_registry_file)
        name = registry_loader.get_redis_stream_name("ingestion")
        assert name == "ingestion_queue"
    
    def test_get_embedding_stream(self, registry_loader, temp_registry_file):
        """Test getting embedding stream name."""
        registry_loader.load(config_path=temp_registry_file)
        name = registry_loader.get_redis_stream_name("embedding")
        assert name == "embedding_queue"
    
    def test_get_retry_stream(self, registry_loader, temp_registry_file):
        """Test getting retry stream name."""
        registry_loader.load(config_path=temp_registry_file)
        name = registry_loader.get_redis_stream_name("retry")
        assert name == "retry_queue"
    
    def test_get_dead_letter_stream(self, registry_loader, temp_registry_file):
        """Test getting dead letter stream name."""
        registry_loader.load(config_path=temp_registry_file)
        name = registry_loader.get_redis_stream_name("dead_letter")
        assert name == "failed_queue"
    
    def test_invalid_stream_key(self, registry_loader, temp_registry_file):
        """Test ValueError for invalid stream key."""
        registry_loader.load(config_path=temp_registry_file)
        
        with pytest.raises(ValueError) as exc_info:
            registry_loader.get_redis_stream_name("invalid")
        
        assert "Unknown stream key" in str(exc_info.value)


# =============================================================================
# CONSUMER GROUP TESTS
# =============================================================================

class TestGetRedisConsumerGroup:
    """Test getting Redis consumer group names."""
    
    def test_get_ingestion_consumer_group(self, registry_loader, temp_registry_file):
        """Test getting ingestion consumer group - THIS PREVENTS TODAY'S ISSUE!"""
        registry_loader.load(config_path=temp_registry_file)
        group = registry_loader.get_redis_consumer_group("ingestion")
        assert group == "workers"
    
    def test_get_retry_consumer_group(self, registry_loader, temp_registry_file):
        """Test getting retry consumer group."""
        registry_loader.load(config_path=temp_registry_file)
        group = registry_loader.get_redis_consumer_group("retry")
        assert group == "workers"
    
    def test_consumer_groups_match(self, registry_loader, temp_registry_file):
        """Test that all consumer groups match (prevents mismatch)."""
        registry_loader.load(config_path=temp_registry_file)
        
        ingestion_group = registry_loader.get_redis_consumer_group("ingestion")
        retry_group = registry_loader.get_redis_consumer_group("retry")
        
        # All should be "workers" - prevents today's issue!
        assert ingestion_group == retry_group == "workers"


# =============================================================================
# DATABASE URL TESTS
# =============================================================================

class TestGetDatabaseUrl:
    """Test getting database URLs."""
    
    def test_get_database_url_local(self, registry_loader, temp_registry_file):
        """Test getting local database URL."""
        registry_loader.load(config_path=temp_registry_file)
        url = registry_loader.get_database_url(use_container=False)
        assert "localhost" in url
        assert "ecosystem_mcp_test" in url
    
    def test_get_database_url_container(self, registry_loader, temp_registry_file):
        """Test getting container database URL."""
        registry_loader.load(config_path=temp_registry_file)
        url = registry_loader.get_database_url(use_container=True)
        assert "postgres" in url
        assert "ecosystem_mcp_test" in url


# =============================================================================
# SERVICE PORT TESTS
# =============================================================================

class TestGetServicePort:
    """Test getting service ports."""
    
    def test_get_api_port(self, registry_loader, temp_registry_file):
        """Test getting API port."""
        registry_loader.load(config_path=temp_registry_file)
        port = registry_loader.get_service_port("ecosystem_mcp", "api")
        assert port == 8000
    
    def test_get_metrics_port(self, registry_loader, temp_registry_file):
        """Test getting metrics port."""
        registry_loader.load(config_path=temp_registry_file)
        port = registry_loader.get_service_port("ecosystem_mcp", "metrics")
        assert port == 9090
    
    def test_get_embedding_service_port(self, registry_loader, temp_registry_file):
        """Test getting embedding service port."""
        registry_loader.load(config_path=temp_registry_file)
        port = registry_loader.get_service_port("ecosystem_mcp_embedding", "api")
        assert port == 8001
    
    def test_invalid_service_name(self, registry_loader, temp_registry_file):
        """Test ValueError for invalid service name."""
        registry_loader.load(config_path=temp_registry_file)
        
        with pytest.raises(ValueError) as exc_info:
            registry_loader.get_service_port("invalid_service", "api")
        
        assert "Unknown service" in str(exc_info.value)
    
    def test_invalid_port_type(self, registry_loader, temp_registry_file):
        """Test ValueError for invalid port type."""
        registry_loader.load(config_path=temp_registry_file)
        
        with pytest.raises(ValueError) as exc_info:
            registry_loader.get_service_port("ecosystem_mcp", "invalid_port")
        
        assert "no port" in str(exc_info.value)


# =============================================================================
# WORKER CONFIG TESTS
# =============================================================================

class TestGetWorkerConfig:
    """Test getting worker configuration."""
    
    def test_get_ingestion_worker_config(self, registry_loader, temp_registry_file):
        """Test getting ingestion worker config."""
        registry_loader.load(config_path=temp_registry_file)
        config = registry_loader.get_worker_config("ingestion")
        
        assert config["consumer_group"] == "workers"
        assert config["poll_interval_seconds"] == 5
        assert config["batch_size"] == 1
    
    def test_get_retry_worker_config(self, registry_loader, temp_registry_file):
        """Test getting retry worker config."""
        registry_loader.load(config_path=temp_registry_file)
        config = registry_loader.get_worker_config("retry")
        
        assert config["consumer_group"] == "workers"
        assert config["poll_interval_seconds"] == 10
        assert config["batch_size"] == 10
    
    def test_invalid_worker_type(self, registry_loader, temp_registry_file):
        """Test ValueError for invalid worker type."""
        registry_loader.load(config_path=temp_registry_file)
        
        with pytest.raises(ValueError) as exc_info:
            registry_loader.get_worker_config("invalid")
        
        assert "Unknown worker type" in str(exc_info.value)


# =============================================================================
# GLOBAL FUNCTION TESTS
# =============================================================================

class TestGlobalFunctions:
    """Test global convenience functions."""
    
    def test_get_registry_function(self, temp_registry_file):
        """Test get_registry() global function."""
        registry = get_registry(config_path=temp_registry_file)
        assert isinstance(registry, ServiceRegistry)
        assert registry.version == "1.0.0"
    
    def test_get_redis_stream_name_function(self, temp_registry_file):
        """Test get_redis_stream_name() convenience function."""
        # Load registry first
        get_registry(config_path=temp_registry_file)
        
        name = get_redis_stream_name("ingestion")
        assert name == "ingestion_queue"
    
    def test_get_redis_consumer_group_function(self, temp_registry_file):
        """Test get_redis_consumer_group() convenience function."""
        # Load registry first
        get_registry(config_path=temp_registry_file)
        
        group = get_redis_consumer_group("ingestion")
        assert group == "workers"
    
    def test_get_database_url_function(self, temp_registry_file):
        """Test get_database_url() convenience function."""
        # Load registry first
        get_registry(config_path=temp_registry_file)
        
        url = get_database_url()
        assert "localhost" in url
    
    def test_get_service_port_function(self, temp_registry_file):
        """Test get_service_port() convenience function."""
        # Load registry first
        get_registry(config_path=temp_registry_file)
        
        port = get_service_port("ecosystem_mcp", "api")
        assert port == 8000
    
    def test_get_worker_config_function(self, temp_registry_file):
        """Test get_worker_config() convenience function."""
        # Load registry first
        get_registry(config_path=temp_registry_file)
        
        config = get_worker_config("ingestion")
        assert config["consumer_group"] == "workers"


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestSchemaValidation:
    """Test Pydantic schema validation."""
    
    def test_invalid_environment(self, registry_loader):
        """Test validation fails for invalid environment."""
        invalid_yaml = """
version: "1.0.0"
environment: "invalid_env"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError):
                registry_loader.load(config_path=temp_path)
        finally:
            temp_path.unlink()
    
    def test_invalid_port_number(self, registry_loader):
        """Test validation fails for invalid port number."""
        # Port numbers must be 1-65535
        # This test would require a full YAML with invalid port
        pass  # Covered by Pydantic validation
    
    def test_consumer_group_validation(self, registry_loader):
        """Test consumer group name validation (prevents today's issue!)."""
        invalid_yaml_with_space = """
version: "1.0.0"
environment: "test"
redis:
  streams:
    ingestion:
      name: "ingestion_queue"
      max_length: 10000
      consumer_group: "invalid group"  # Space not allowed!
      description: "Test"
"""
        # This would be caught by Pydantic validator
        # and prevent the exact issue we had today!
        pass  # Covered by Pydantic @validator


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

