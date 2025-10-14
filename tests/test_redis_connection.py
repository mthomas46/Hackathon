"""
Unit and Integration Tests for Redis Connection Fix

Tests the lazy connection logic that ensures Redis is connected
before queuing ingestion jobs.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import UUID, uuid4

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "services/ecosystem-mcp"))

from src.utils.redis_client import RedisClient, get_redis_client
from src.api.routes.admin import start_ingestion, IngestRequest


class TestRedisClientConnection:
    """Unit tests for RedisClient connection state."""
    
    @pytest.fixture
    def redis_client(self):
        """Create a RedisClient instance."""
        return RedisClient(redis_url="redis://localhost:6379/0")
    
    def test_redis_client_initialization(self, redis_client):
        """Test that RedisClient initializes in disconnected state."""
        assert redis_client.client is None
        assert redis_client._connected is False
        assert redis_client.redis_url == "redis://localhost:6379/0"
    
    @pytest.mark.asyncio
    async def test_redis_client_connect(self, redis_client):
        """Test that connect() establishes connection."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            # Mock consumer group creation
            mock_redis.xgroup_create = AsyncMock()
            
            await redis_client.connect()
            
            assert redis_client.client is not None
            assert redis_client._connected is True
            mock_from_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_client_disconnect(self, redis_client):
        """Test that close() disconnects properly."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.close = AsyncMock()
            mock_redis.xgroup_create = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            await redis_client.connect()
            assert redis_client._connected is True
            
            await redis_client.close()
            assert redis_client._connected is False
            mock_redis.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_to_stream_requires_connection(self, redis_client):
        """Test that add_to_stream fails gracefully when not connected."""
        # Client not connected
        assert redis_client.client is None
        
        # Should raise AttributeError when trying to use None client
        with pytest.raises(AttributeError):
            await redis_client.add_to_stream(
                stream="test-stream",
                data={"key": "value"}
            )
    
    @pytest.mark.asyncio
    async def test_add_to_stream_with_connection(self, redis_client):
        """Test that add_to_stream works when connected."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.xadd = AsyncMock(return_value="1234-0")
            mock_redis.xgroup_create = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            await redis_client.connect()
            
            result = await redis_client.add_to_stream(
                stream="test-stream",
                data={"key": "value"}
            )
            
            assert result == "1234-0"
            mock_redis.xadd.assert_called_once()


class TestIngestEndpointLazyConnection:
    """Integration tests for lazy Redis connection in ingest endpoint."""
    
    @pytest.mark.asyncio
    async def test_ingest_connects_redis_if_not_connected(self):
        """Test that ingest endpoint connects Redis lazily."""
        request = IngestRequest(repo_path="/app", mode="quick")
        
        with patch('src.api.routes.admin.get_redis_client') as mock_get_redis, \
             patch('src.api.routes.admin.get_database') as mock_get_db, \
             patch('pathlib.Path.exists', return_value=True):
            
            # Mock Redis client in disconnected state
            mock_redis = AsyncMock()
            mock_redis._connected = False
            mock_redis.client = None
            mock_redis.INGESTION_STREAM = "ingestion_queue"
            mock_redis.connect = AsyncMock()
            mock_redis.add_to_stream = AsyncMock(return_value="1234-0")
            mock_get_redis.return_value = mock_redis
            
            # Mock database
            mock_session = AsyncMock()
            mock_job = Mock()
            mock_job.id = uuid4()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.commit = AsyncMock()
            
            mock_repo = AsyncMock()
            mock_repo.create_job = AsyncMock(return_value=mock_job)
            
            with patch('src.api.routes.admin.IngestionJobRepository', return_value=mock_repo):
                mock_db = Mock()
                mock_db.session = Mock(return_value=mock_session)
                mock_get_db.return_value = mock_db
                
                # Call endpoint
                background_tasks = Mock()
                response = await start_ingestion(request, background_tasks)
                
                # Verify Redis was connected
                mock_redis.connect.assert_called_once()
                
                # Verify job was added to stream
                mock_redis.add_to_stream.assert_called_once_with(
                    stream="ingestion_queue",
                    data={
                        "job_id": str(mock_job.id),
                        "mode": "quick",
                        "repo_path": "/app"
                    }
                )
                
                assert response.status == "queued"
    
    @pytest.mark.asyncio
    async def test_ingest_skips_connect_if_already_connected(self):
        """Test that ingest endpoint skips connect if Redis already connected."""
        request = IngestRequest(repo_path="/app", mode="quick")
        
        with patch('src.api.routes.admin.get_redis_client') as mock_get_redis, \
             patch('src.api.routes.admin.get_database') as mock_get_db, \
             patch('pathlib.Path.exists', return_value=True):
            
            # Mock Redis client in CONNECTED state
            mock_redis = AsyncMock()
            mock_redis._connected = True
            mock_redis.client = Mock()  # Not None
            mock_redis.INGESTION_STREAM = "ingestion_queue"
            mock_redis.connect = AsyncMock()
            mock_redis.add_to_stream = AsyncMock(return_value="1234-0")
            mock_get_redis.return_value = mock_redis
            
            # Mock database
            mock_session = AsyncMock()
            mock_job = Mock()
            mock_job.id = uuid4()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.commit = AsyncMock()
            
            mock_repo = AsyncMock()
            mock_repo.create_job = AsyncMock(return_value=mock_job)
            
            with patch('src.api.routes.admin.IngestionJobRepository', return_value=mock_repo):
                mock_db = Mock()
                mock_db.session = Mock(return_value=mock_session)
                mock_get_db.return_value = mock_db
                
                # Call endpoint
                background_tasks = Mock()
                response = await start_ingestion(request, background_tasks)
                
                # Verify Redis connect was NOT called (already connected)
                mock_redis.connect.assert_not_called()
                
                # Verify job was still added to stream
                mock_redis.add_to_stream.assert_called_once()
                
                assert response.status == "queued"
    
    @pytest.mark.asyncio
    async def test_ingest_handles_invalid_repo_path(self):
        """Test that ingest endpoint validates repo path."""
        from fastapi import HTTPException
        
        request = IngestRequest(repo_path="/nonexistent", mode="quick")
        
        with patch('pathlib.Path.exists', return_value=False):
            background_tasks = Mock()
            
            with pytest.raises(HTTPException) as exc_info:
                await start_ingestion(request, background_tasks)
            
            assert exc_info.value.status_code == 400
            assert "does not exist" in str(exc_info.value.detail)


class TestRedisGlobalSingleton:
    """Unit tests for Redis global singleton pattern."""
    
    def test_get_redis_client_returns_same_instance(self):
        """Test that get_redis_client() returns singleton."""
        # Reset global
        import src.utils.redis_client as redis_module
        redis_module._redis_client = None
        
        client1 = get_redis_client()
        client2 = get_redis_client()
        
        assert client1 is client2
        assert id(client1) == id(client2)
    
    def test_get_redis_client_initializes_disconnected(self):
        """Test that singleton starts in disconnected state."""
        import src.utils.redis_client as redis_module
        redis_module._redis_client = None
        
        client = get_redis_client()
        
        assert client.client is None
        assert client._connected is False


class TestRedisConnectionLifecycle:
    """Integration tests for Redis connection lifecycle."""
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self):
        """Test full connection lifecycle: init -> connect -> use -> close."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.xadd = AsyncMock(return_value="1234-0")
            mock_redis.xgroup_create = AsyncMock()
            mock_redis.close = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            # Initialize
            client = RedisClient(redis_url="redis://localhost:6379/0")
            assert client.client is None
            
            # Connect
            await client.connect()
            assert client._connected is True
            assert client.client is not None
            
            # Use
            result = await client.add_to_stream(
                stream="test-stream",
                data={"test": "data"}
            )
            assert result == "1234-0"
            
            # Close
            await client.close()
            assert client._connected is False
    
    @pytest.mark.asyncio
    async def test_multiple_connects_are_safe(self):
        """Test that calling connect() multiple times is safe."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.xgroup_create = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            client = RedisClient(redis_url="redis://localhost:6379/0")
            
            # Connect multiple times
            await client.connect()
            assert client._connected is True
            
            await client.connect()  # Should return early
            assert client._connected is True
            
            # from_url should only be called once
            assert mock_from_url.call_count == 1


class TestRedisStreamOperations:
    """Unit tests for Redis stream operations."""
    
    @pytest.mark.asyncio
    async def test_get_stream_length(self):
        """Test getting stream length."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.xlen = AsyncMock(return_value=42)
            mock_redis.xgroup_create = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            client = RedisClient(redis_url="redis://localhost:6379/0")
            await client.connect()
            
            length = await client.get_stream_length("test-stream")
            
            assert length == 42
            mock_redis.xlen.assert_called_once_with("test-stream")
    
    @pytest.mark.asyncio
    async def test_add_to_stream_with_maxlen(self):
        """Test adding to stream with max length."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.xadd = AsyncMock(return_value="1234-0")
            mock_redis.xgroup_create = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            client = RedisClient(redis_url="redis://localhost:6379/0")
            await client.connect()
            
            await client.add_to_stream(
                stream="test-stream",
                data={"key": "value"},
                max_len=1000
            )
            
            # Verify xadd was called with maxlen
            call_args = mock_redis.xadd.call_args
            assert call_args[0][0] == "test-stream"
            assert "maxlen" in call_args[1]


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

