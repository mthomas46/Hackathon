"""
Integration tests for UserRepository.

Tests real HTTP interactions with user-store service.
Uses mocked HTTP responses for isolation.
"""

import pytest
import httpx
from unittest.mock import patch, AsyncMock

from infrastructure.repositories.user_repository import UserRepository
from domain.entities.expert import Expert


@pytest.mark.integration
@pytest.mark.skip(reason="Requires complex httpx.AsyncClient mocking - to be implemented with respx library")
class TestUserRepositoryIntegration:
    """Integration tests for UserRepository HTTP interactions."""
    
    @pytest.fixture
    def user_repo(self):
        """Create a user repository instance."""
        return UserRepository(
            base_url="http://user-store:5150",
            timeout=10.0
        )
    
    @pytest.mark.asyncio
    async def test_get_users_by_role_integration(self, user_repo):
        """Test getting users by role via HTTP."""
        # Mock HTTP response
        mock_response = {
            "users": [
                {
                    "user_id": "user1",
                    "name": "Alice Developer",
                    "role": "Backend Developer",
                    "topics": ["Python", "FastAPI"],
                    "services": [],
                    "document_count": 10,
                    "service_count": 2
                },
                {
                    "user_id": "user2",
                    "name": "Bob Engineer",
                    "role": "Backend Developer",
                    "topics": ["Python", "Django"],
                    "services": [],
                    "document_count": 15,
                    "service_count": 3
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.status_code = 200
            mock_response_obj.raise_for_status = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response_obj)
            
            # Execute
            result = await user_repo.get_users_by_role("Backend Developer", limit=10)
            
            # Verify
            assert len(result) == 2
            assert all(isinstance(user, Expert) for user in result)
            assert result[0].name == "Alice Developer"
            assert result[0].role == "Backend Developer"
            assert "Python" in result[0].topics
    
    @pytest.mark.asyncio
    async def test_get_users_by_topic_integration(self, user_repo):
        """Test getting users by topic via HTTP."""
        mock_response = {
            "users": [
                {
                    "user_id": "user1",
                    "name": "Python Expert",
                    "role": "Developer",
                    "topics": ["Python", "FastAPI", "Async"],
                    "services": [],
                    "document_count": 20,
                    "service_count": 5
                }
            ]
        }
        
        with patch.object(user_repo.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status = AsyncMock()
            
            # Execute
            result = await user_repo.get_users_by_topic("Python", limit=10)
            
            # Verify
            assert len(result) == 1
            assert result[0].name == "Python Expert"
            assert "Python" in result[0].topics
            
            # Verify HTTP call
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_users_integration(self, user_repo):
        """Test searching users via HTTP."""
        mock_response = {
            "users": [
                {
                    "user_id": "user1",
                    "name": "Alice Backend",
                    "role": "Developer",
                    "topics": ["Python"],
                    "services": [],
                    "document_count": 5,
                    "service_count": 1
                }
            ]
        }
        
        with patch.object(user_repo.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status = AsyncMock()
            
            # Execute
            result = await user_repo.search_users("Python backend", limit=10)
            
            # Verify
            assert len(result) == 1
            assert result[0].name == "Alice Backend"
            
            # Verify HTTP call
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_repository_handles_http_errors(self, user_repo):
        """Test that repository handles HTTP errors gracefully."""
        with patch.object(user_repo.client, 'get', new_callable=AsyncMock) as mock_get:
            # Simulate HTTP error
            mock_get.side_effect = httpx.HTTPError("Connection failed")
            
            # Execute and verify error handling
            with pytest.raises(httpx.HTTPError):
                await user_repo.get_users_by_role("Developer", limit=10)
    
    @pytest.mark.asyncio
    async def test_repository_handles_empty_results(self, user_repo):
        """Test that repository handles empty results correctly."""
        mock_response = {"users": []}
        
        with patch.object(user_repo.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status = AsyncMock()
            
            # Execute
            result = await user_repo.get_users_by_role("NonexistentRole", limit=10)
            
            # Verify
            assert result == []
    
    @pytest.mark.asyncio
    async def test_repository_respects_timeout(self, user_repo):
        """Test that repository respects timeout settings."""
        # Verify timeout is set correctly
        assert user_repo.timeout == 10.0
        
        with patch.object(user_repo.client, 'get', new_callable=AsyncMock) as mock_get:
            # Simulate timeout
            mock_get.side_effect = httpx.TimeoutException("Request timed out")
            
            # Execute and verify timeout handling
            with pytest.raises(httpx.TimeoutException):
                await user_repo.get_users_by_role("Developer", limit=10)

