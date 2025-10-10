"""
Unit tests for infrastructure repositories.

Tests BaseRepository, UserRepository, DocumentRepository, ServiceRepository
with mocked HTTP responses.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, Mock

from infrastructure.repositories.base_repository import BaseRepository
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.document_repository import DocumentRepository
from infrastructure.repositories.service_repository import ServiceRepository


class TestBaseRepository:
    """Tests for BaseRepository."""
    
    @pytest.fixture
    def base_repo(self):
        """Create a base repository instance."""
        return BaseRepository(base_url="http://test-service:8000", timeout=5.0)
    
    def test_initialization(self, base_repo):
        """Test repository can be initialized."""
        assert base_repo.base_url == "http://test-service:8000"
        assert base_repo.timeout == 5.0
    
    def test_base_url_formatting(self):
        """Test that base URL is properly formatted."""
        repo = BaseRepository(base_url="http://test-service:8000/", timeout=5.0)
        assert not repo.base_url.endswith("/")  # Should strip trailing slash
    
    def test_timeout_is_positive(self, base_repo):
        """Test that timeout is a positive value."""
        assert base_repo.timeout > 0


class TestUserRepository:
    """Tests for UserRepository."""
    
    @pytest.fixture
    def user_repo(self):
        """Create a user repository instance."""
        return UserRepository(base_url="http://user-store:5150", timeout=10.0)
    
    def test_initialization(self, user_repo):
        """Test repository can be initialized."""
        assert user_repo.base_url == "http://user-store:5150"
        assert user_repo.timeout == 10.0
    
    def test_inherits_from_base_repository(self, user_repo):
        """Test that UserRepository inherits from BaseRepository."""
        assert isinstance(user_repo, BaseRepository)


class TestDocumentRepository:
    """Tests for DocumentRepository."""
    
    @pytest.fixture
    def doc_repo(self):
        """Create a document repository instance."""
        return DocumentRepository(base_url="http://doc-store:5087", timeout=10.0)
    
    def test_initialization(self, doc_repo):
        """Test repository can be initialized."""
        assert doc_repo.base_url == "http://doc-store:5087"
        assert doc_repo.timeout == 10.0
    
    def test_inherits_from_base_repository(self, doc_repo):
        """Test that DocumentRepository inherits from BaseRepository."""
        assert isinstance(doc_repo, BaseRepository)


class TestServiceRepository:
    """Tests for ServiceRepository."""
    
    @pytest.fixture
    def service_repo(self):
        """Create a service repository instance."""
        return ServiceRepository(
            base_url="http://external-service-store:5140",
            timeout=10.0
        )
    
    def test_initialization(self, service_repo):
        """Test repository can be initialized."""
        assert service_repo.base_url == "http://external-service-store:5140"
        assert service_repo.timeout == 10.0
    
    def test_inherits_from_base_repository(self, service_repo):
        """Test that ServiceRepository inherits from BaseRepository."""
        assert isinstance(service_repo, BaseRepository)

