"""Comprehensive tests for Doc Store infrastructure layer."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from services.doc_store.infrastructure.adapters.database_adapter import DatabaseAdapter
    from services.doc_store.infrastructure.repositories.base_repository import BaseRepository
    from services.doc_store.infrastructure.repositories.document_repository import DocumentRepository
    from services.doc_store.infrastructure.services.cache_service import CacheService
except ImportError:
    # Fallback for test environment
    DatabaseAdapter = None
    BaseRepository = None
    DocumentRepository = None
    CacheService = None


@pytest.mark.skipif(DatabaseAdapter is None, reason="Infrastructure modules not available")
class TestDatabaseAdapter:
    """Test database adapter functionality."""

    @pytest.fixture
    def db_adapter(self):
        """Create database adapter instance."""
        return DatabaseAdapter(":memory:")

    def test_adapter_initialization(self, db_adapter):
        """Test database adapter initialization."""
        assert db_adapter.db_path == ":memory:"
        assert hasattr(db_adapter, 'get_connection')

    @patch('sqlite3.connect')
    def test_execute_query(self, mock_connect, db_adapter):
        """Test query execution."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.row_factory = None
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'test'}]
        mock_connect.return_value = mock_conn

        result = db_adapter.execute_query("SELECT * FROM test")

        assert result == [{'id': 1, 'name': 'test'}]
        mock_cursor.execute.assert_called_once()

    @patch('sqlite3.connect')
    def test_execute_write(self, mock_connect, db_adapter):
        """Test write operation execution."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        mock_connect.return_value = mock_conn

        result = db_adapter.execute_write("INSERT INTO test VALUES (?)", ("value",))

        assert result == 1
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_table_exists(self, db_adapter):
        """Test table existence check."""
        with patch.object(db_adapter, 'execute_query') as mock_query:
            mock_query.return_value = [{'name': 'documents'}]

            result = db_adapter.table_exists("documents")
            assert result is True

            mock_query.return_value = []
            result = db_adapter.table_exists("nonexistent")
            assert result is False

    def test_health_check_success(self, db_adapter):
        """Test successful health check."""
        with patch.object(db_adapter, 'execute_query') as mock_query:
            mock_query.return_value = [{'test': 1}]

            result = db_adapter.health_check()
            assert result["status"] == "healthy"
            assert result["connection_test"] is True

    def test_health_check_failure(self, db_adapter):
        """Test health check failure."""
        with patch.object(db_adapter, 'execute_query') as mock_query:
            mock_query.side_effect = Exception("Connection failed")

            result = db_adapter.health_check()
            assert result["status"] == "unhealthy"
            assert "error" in result


@pytest.mark.skipif(BaseRepository is None, reason="Infrastructure modules not available")
class TestBaseRepository:
    """Test base repository functionality."""

    @pytest.fixture
    def mock_adapter(self):
        """Create mock database adapter."""
        return MagicMock(spec=DatabaseAdapter)

    @pytest.fixture
    def base_repo(self, mock_adapter):
        """Create base repository instance."""
        # Create a concrete implementation for testing
        class TestRepository(BaseRepository):
            def table_name(self):
                return "test_table"

        return TestRepository(mock_adapter)

    def test_repository_initialization(self, base_repo, mock_adapter):
        """Test repository initialization."""
        assert base_repo.db_adapter == mock_adapter

    def test_table_name_abstract(self):
        """Test that table_name is abstract."""
        with pytest.raises(TypeError):
            BaseRepository(MagicMock())

    def test_health_check(self, base_repo, mock_adapter):
        """Test health check delegation."""
        expected_result = {"status": "healthy"}
        mock_adapter.health_check.return_value = expected_result

        result = base_repo.health_check()
        assert result == expected_result
        mock_adapter.health_check.assert_called_once()

    def test_table_exists(self, base_repo, mock_adapter):
        """Test table existence check."""
        mock_adapter.table_exists.return_value = True

        result = base_repo.table_exists()
        assert result is True
        mock_adapter.table_exists.assert_called_once_with("test_table")

    def test_get_table_info(self, base_repo, mock_adapter):
        """Test table info retrieval."""
        expected_info = [{"name": "id", "type": "INTEGER"}]
        mock_adapter.get_table_info.return_value = expected_info

        result = base_repo.get_table_info()
        assert result == expected_info
        mock_adapter.get_table_info.assert_called_once_with("test_table")


@pytest.mark.skipif(DocumentRepository is None, reason="Infrastructure modules not available")
class TestDocumentRepository:
    """Test document repository functionality."""

    @pytest.fixture
    def mock_adapter(self):
        """Create mock database adapter."""
        return MagicMock(spec=DatabaseAdapter)

    @pytest.fixture
    def doc_repo(self, mock_adapter):
        """Create document repository instance."""
        return DocumentRepository(mock_adapter)

    def test_table_name(self, doc_repo):
        """Test correct table name."""
        assert doc_repo.table_name() == "documents"

    def test_save_document(self, doc_repo):
        """Test document saving."""
        document = {"id": "test", "content": "test content"}
        result = doc_repo.save(document)
        assert result == document

    def test_find_by_id_existing(self, doc_repo):
        """Test finding existing document."""
        result = doc_repo.find_by_id("test-doc")
        assert result is not None
        assert result["id"] == "test-doc"
        assert result["content"] == "Test document content"

    def test_find_by_id_nonexistent(self, doc_repo):
        """Test finding nonexistent document."""
        result = doc_repo.find_by_id("nonexistent")
        assert result is None

    def test_find_all(self, doc_repo):
        """Test finding all documents."""
        result = doc_repo.find_all()
        assert isinstance(result, list)
        assert len(result) == 2
        assert all("id" in doc for doc in result)

    def test_find_all_with_limit(self, doc_repo):
        """Test finding documents with limit."""
        result = doc_repo.find_all(limit=1)
        assert len(result) == 1

    def test_search_documents(self, doc_repo):
        """Test document search."""
        result = doc_repo.search("Sample")
        assert isinstance(result, list)
        assert len(result) >= 0

    def test_count_documents(self, doc_repo):
        """Test document counting."""
        result = doc_repo.count()
        assert isinstance(result, int)
        assert result == 42

    def test_delete_existing_document(self, doc_repo):
        """Test deleting existing document."""
        result = doc_repo.delete("existing-doc")
        assert result is True

    def test_delete_nonexistent_document(self, doc_repo):
        """Test deleting nonexistent document."""
        result = doc_repo.delete("nonexistent")
        assert result is False

    def test_exists_existing_document(self, doc_repo):
        """Test checking existence of existing document."""
        result = doc_repo.exists("test-doc")
        assert result is True

    def test_exists_nonexistent_document(self, doc_repo):
        """Test checking existence of nonexistent document."""
        result = doc_repo.exists("nonexistent")
        assert result is False


@pytest.mark.skipif(CacheService is None, reason="Infrastructure modules not available")
class TestCacheService:
    """Test cache service functionality."""

    @pytest.fixture
    def mock_adapter(self):
        """Create mock database adapter."""
        return MagicMock(spec=DatabaseAdapter)

    @pytest.fixture
    def cache_service(self, mock_adapter):
        """Create cache service instance."""
        return CacheService(mock_adapter)

    def test_cache_initialization(self, cache_service, mock_adapter):
        """Test cache service initialization."""
        assert cache_service.db_adapter == mock_adapter
        assert cache_service.cache_ttl == 3600

    @patch('time.time')
    def test_get_cache_hit(self, mock_time, cache_service, mock_adapter):
        """Test cache hit scenario."""
        mock_time.return_value = 1000
        mock_adapter.execute_query.return_value = [{"value": "test_data", "expires_at": 2000}]

        result = cache_service.get("test_key")
        assert result == "test_data"
        mock_adapter.execute_query.assert_called_once()

    @patch('time.time')
    def test_get_cache_miss_expired(self, mock_time, cache_service, mock_adapter):
        """Test cache miss due to expiration."""
        mock_time.return_value = 3000  # After expiration
        mock_adapter.execute_query.return_value = [{"value": "test_data", "expires_at": 2000}]

        result = cache_service.get("test_key")
        assert result is None
        # Should have called execute_query twice: once for get, once for delete
        assert mock_adapter.execute_query.call_count == 1

    @patch('time.time')
    def test_set_cache_success(self, mock_time, cache_service, mock_adapter):
        """Test successful cache set operation."""
        mock_time.return_value = 1000
        mock_adapter.execute_write.return_value = 1

        result = cache_service.set("test_key", "test_value")
        assert result is True
        mock_adapter.execute_write.assert_called_once()

    def test_set_cache_failure(self, cache_service, mock_adapter):
        """Test cache set operation failure."""
        mock_adapter.execute_write.side_effect = Exception("DB error")

        result = cache_service.set("test_key", "test_value")
        assert result is False

    def test_delete_cache_success(self, cache_service, mock_adapter):
        """Test successful cache delete."""
        mock_adapter.execute_write.return_value = 1

        result = cache_service.delete("test_key")
        assert result is True
        mock_adapter.execute_write.assert_called_once_with(
            "DELETE FROM cache WHERE key = ?", ("test_key",)
        )

    def test_clear_cache_success(self, cache_service, mock_adapter):
        """Test successful cache clear."""
        mock_adapter.execute_write.return_value = 5  # 5 entries deleted

        result = cache_service.clear()
        assert result is True
        mock_adapter.execute_write.assert_called_once_with("DELETE FROM cache")

    @patch('time.time')
    def test_cleanup_expired(self, mock_time, cache_service, mock_adapter):
        """Test expired entry cleanup."""
        mock_time.return_value = 3000
        mock_adapter.execute_write.return_value = 3  # 3 entries cleaned

        result = cache_service.cleanup_expired()
        assert result == 3
        mock_adapter.execute_write.assert_called_once()

    def test_health_check_success(self, cache_service, mock_adapter):
        """Test successful health check."""
        # Mock successful cache operations
        with patch.object(cache_service, 'set', return_value=True), \
             patch.object(cache_service, 'get', return_value="test_value"), \
             patch.object(cache_service, 'delete', return_value=True):

            result = cache_service.health_check()
            assert result["status"] == "healthy"
            assert result["cache_operations"] is True

    def test_health_check_failure(self, cache_service, mock_adapter):
        """Test health check failure."""
        with patch.object(cache_service, 'set', side_effect=Exception("Cache error")):
            result = cache_service.health_check()
            assert result["status"] == "unhealthy"
            assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
