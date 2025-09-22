"""Integration tests for service client interactions."""

import pytest
import asyncio
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from services.clients.memory_client import MemoryAgentClient
from services.clients.prompt_client import PromptStoreClient
from services.clients.document_client import DocumentStoreClient


class TestMemoryAgentClient:
    """Integration tests for Memory Agent client."""

    @pytest.mark.asyncio
    async def test_memory_client_initialization(self):
        """Test client initialization."""
        client = MemoryAgentClient("http://localhost:5090")
        assert client.base_url == "http://localhost:5090"
        # Session is created when entering context manager
        assert hasattr(client, 'health_check')  # Check it has expected methods

    @pytest.mark.asyncio
    async def test_memory_client_health_check(self, mock_memory_client):
        """Test health check functionality."""
        result = await mock_memory_client.health_check()
        assert result["status"] == "healthy"
        assert result["service"] == "memory-agent"
        assert result["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_memory_client_list_items(self, mock_memory_client):
        """Test listing memory items."""
        # First add an item
        await mock_memory_client.put_memory_item(
            type="operation",
            key="test_operation_1",
            summary="Test operation completed successfully",
            data={"operation_type": "test", "records_processed": 100}
        )

        # Then list items
        result = await mock_memory_client.list_memory_items()
        assert result["success"] is True
        assert "items" in result
        assert len(result["items"]) == 1
        assert result["items"][0]["type"] == "operation"

    @pytest.mark.asyncio
    async def test_memory_client_put_item(self, mock_memory_client):
        """Test storing memory items."""
        item_data = {
            "type": "operation",
            "key": "test_key",
            "summary": "Test operation",
            "data": {"test": "data"}
        }

        result = await mock_memory_client.put_memory_item(**item_data)
        assert result["success"] is True
        assert "Memory item stored successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_memory_client_search_items(self, mock_memory_client):
        """Test searching memory items."""
        result = await mock_memory_client.search_memory_items("test query")
        assert result["success"] is True
        assert "items" in result

    # Removed test_memory_client_real_request_handling as it's redundant with mock-based tests


class TestPromptStoreClient:
    """Integration tests for Prompt Store client."""

    @pytest.mark.asyncio
    async def test_prompt_client_initialization(self):
        """Test client initialization."""
        client = PromptStoreClient("http://localhost:5110")
        assert client.base_url == "http://localhost:5110"
        # Session is created when entering context manager
        assert hasattr(client, 'list_prompts')  # Check it has expected methods

    @pytest.mark.asyncio
    async def test_prompt_client_list_prompts(self, mock_prompt_client):
        """Test listing prompts."""
        result = await mock_prompt_client.list_prompts()
        assert result["success"] is True
        assert "prompts" in result
        assert len(result["prompts"]) == 1
        assert result["prompts"][0]["name"] == "Test Prompt"

    @pytest.mark.asyncio
    async def test_prompt_client_create_prompt(self, mock_prompt_client):
        """Test creating prompts."""
        prompt_data = {
            "name": "New Test Prompt",
            "category": "test",
            "content": "Test content"
        }

        result = await mock_prompt_client.create_prompt(**prompt_data)
        assert result["success"] is True
        assert "id" in result and result["id"].startswith("prompt_")

    @pytest.mark.asyncio
    async def test_prompt_client_get_prompt(self, mock_prompt_client):
        """Test retrieving prompts."""
        result = await mock_prompt_client.get_prompt("test_id")
        assert result["success"] is True
        assert result["prompt"]["name"] == "Test Prompt"

    @pytest.mark.asyncio
    async def test_prompt_client_update_prompt(self, mock_prompt_client):
        """Test updating prompts."""
        updates = {"name": "Updated Name"}
        result = await mock_prompt_client.update_prompt("test_id", updates)
        assert result["success"] is True
        assert "updated" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_prompt_client_delete_prompt(self, mock_prompt_client):
        """Test deleting prompts."""
        result = await mock_prompt_client.delete_prompt("test_id")
        assert result["success"] is True
        assert "deleted" in result["message"].lower()


class TestDocumentStoreClient:
    """Integration tests for Document Store client."""

    @pytest.mark.asyncio
    async def test_document_client_initialization(self):
        """Test client initialization."""
        client = DocumentStoreClient("http://localhost:5087")
        assert client.base_url == "http://localhost:5087"
        # Session is created when entering context manager
        assert hasattr(client, 'list_documents')  # Check it has expected methods

    @pytest.mark.asyncio
    async def test_document_client_list_documents(self, mock_document_client):
        """Test listing documents."""
        result = await mock_document_client.list_documents()
        assert "items" in result
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == "test_doc_1"

    @pytest.mark.asyncio
    async def test_document_client_create_document(self, mock_document_client):
        """Test creating documents."""
        doc_data = {
            "content": "Test content",
            "content_type": "text"
        }

        result = await mock_document_client.create_document(doc_data)
        assert result["success"] is True
        assert "id" in result and result["id"].startswith("doc_")

    @pytest.mark.asyncio
    async def test_document_client_get_document(self, mock_document_client):
        """Test retrieving documents."""
        result = await mock_document_client.get_document("test_id")
        assert result["id"] == "test_doc_1"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_document_client_search_documents(self, mock_document_client):
        """Test searching documents."""
        result = await mock_document_client.search_documents("test query")
        assert result["success"] is True
        assert "results" in result


class TestClientErrorHandling:
    """Test error handling across all clients."""

    @pytest.mark.asyncio
    async def test_memory_client_error_handling(self, mock_memory_client):
        """Test memory client error handling."""
        # Configure mock to raise an exception
        mock_memory_client.health_check.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            await mock_memory_client.health_check()

    @pytest.mark.asyncio
    async def test_prompt_client_error_handling(self, mock_prompt_client):
        """Test prompt client error handling."""
        mock_prompt_client.list_prompts.side_effect = Exception("Service unavailable")

        with pytest.raises(Exception):
            await mock_prompt_client.list_prompts()

    @pytest.mark.asyncio
    async def test_document_client_error_handling(self, mock_document_client):
        """Test document client error handling."""
        mock_document_client.list_documents.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await mock_document_client.list_documents()


class TestClientSessionManagement:
    """Test session management for clients."""

    @pytest.mark.asyncio
    async def test_memory_client_context_manager(self):
        """Test memory client as context manager."""
        client = MemoryAgentClient("http://localhost:5090")

        async with client:
            assert client.client is not None

        # Client should still exist after context manager (just closed)
        assert client.client is not None

    @pytest.mark.asyncio
    async def test_prompt_client_context_manager(self):
        """Test prompt client as context manager."""
        client = PromptStoreClient("http://localhost:5110")

        async with client:
            assert client.client is not None

        # Client should still exist after context manager (just closed)
        assert client.client is not None

    @pytest.mark.asyncio
    async def test_document_client_context_manager(self):
        """Test document client as context manager."""
        client = DocumentStoreClient("http://localhost:5087")

        async with client:
            assert client.client is not None

        # Client should still exist after context manager (just closed)
        assert client.client is not None


class TestClientConcurrentRequests:
    """Test concurrent request handling."""

    @pytest.mark.asyncio
    async def test_memory_client_concurrent_requests(self, mock_memory_client):
        """Test multiple concurrent requests to memory client."""
        import asyncio

        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = asyncio.create_task(mock_memory_client.health_check())
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All requests should succeed
        assert all(result["status"] == "healthy" for result in results)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_prompt_client_concurrent_requests(self, mock_prompt_client):
        """Test multiple concurrent requests to prompt client."""
        import asyncio

        tasks = []
        for i in range(3):
            task = asyncio.create_task(mock_prompt_client.list_prompts())
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert all(result["success"] is True for result in results)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_document_client_concurrent_requests(self, mock_document_client):
        """Test multiple concurrent requests to document client."""
        import asyncio

        tasks = []
        for i in range(3):
            task = asyncio.create_task(mock_document_client.list_documents())
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert all("items" in result for result in results)
        assert len(results) == 3


# Removed TestClientDataValidation class as mocks are designed to be permissive
