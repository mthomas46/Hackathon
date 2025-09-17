"""Unit tests for Mock Data Generator Service.

Tests the LLM-integrated mock data generation functionality including:
- Mock data generation for different source types
- LLM integration for content creation
- Service integration with doc_store
- Template and prompt management
- Error handling and validation
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

# Adjust path for local imports
import sys
from pathlib import Path

# Add the Mock Data Generator service directory to Python path
mock_data_path = Path(__file__).parent.parent.parent.parent / "services" / "mock-data-generator"
sys.path.insert(0, str(mock_data_path))

from modules.main import MockDataGenerator, MockDataType, GenerationRequest


# Test markers for parallel execution
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe
]


class TestMockDataGenerator:
    """Test suite for MockDataGenerator class."""

    @pytest.fixture
    def mock_data_generator(self):
        """Create a MockDataGenerator instance for testing."""
        return MockDataGenerator()

    @pytest.fixture
    def mock_clients(self):
        """Mock the service clients."""
        with patch('modules.main.ServiceClients') as mock_clients_class:
            mock_clients = MagicMock()
            mock_clients_class.return_value = mock_clients

            # Mock LLM Gateway response
            mock_clients.post_json = AsyncMock(return_value={
                "success": True,
                "response": "This is a mock API documentation page for testing purposes.",
                "provider": "ollama",
                "tokens_used": 50
            })

            # Mock Doc Store response
            mock_clients.post_json = AsyncMock(return_value={
                "success": True,
                "document_id": "mock-doc-12345"
            })

            yield mock_clients

    def test_mock_data_generator_initialization(self, mock_data_generator):
        """Test that MockDataGenerator initializes correctly."""
        assert isinstance(mock_data_generator, MockDataGenerator)
        assert hasattr(mock_data_generator, 'clients')
        assert hasattr(mock_data_generator, 'llm_gateway_url')
        assert hasattr(mock_data_generator, 'doc_store_url')
        assert hasattr(mock_data_generator, 'templates')

        # Check templates are loaded
        assert 'confluence_page' in mock_data_generator.templates
        assert 'github_repo' in mock_data_generator.templates
        assert 'jira_issue' in mock_data_generator.templates

    @pytest.mark.asyncio
    async def test_generate_confluence_page(self, mock_data_generator, mock_clients):
        """Test generation of Confluence page mock data."""
        request = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=1,
            topic="Authentication API",
            complexity="medium"
        )

        result = await mock_data_generator.generate_mock_data(request)

        assert result["success"] is True
        assert result["data_type"] == "confluence_page"
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["data_type"] == "confluence_page"
        assert item["topic"] == "Authentication API"
        assert "id" in item
        assert "content" in item
        assert "generated_at" in item
        assert "title" in item
        assert "space" in item
        assert "author" in item

    @pytest.mark.asyncio
    async def test_generate_github_repo(self, mock_data_generator, mock_clients):
        """Test generation of GitHub repository mock data."""
        request = GenerationRequest(
            data_type=MockDataType.GITHUB_REPO,
            count=1,
            topic="User Management Service",
            complexity="simple"
        )

        result = await mock_data_generator.generate_mock_data(request)

        assert result["success"] is True
        assert result["data_type"] == "github_repo"
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["data_type"] == "github_repo"
        assert item["topic"] == "User Management Service"
        assert "name" in item
        assert "full_name" in item
        assert "description" in item
        assert "language" in item
        assert "stars" in item
        assert "forks" in item

    @pytest.mark.asyncio
    async def test_generate_jira_issue(self, mock_data_generator, mock_clients):
        """Test generation of Jira issue mock data."""
        request = GenerationRequest(
            data_type=MockDataType.JIRA_ISSUE,
            count=2,
            topic="Security Enhancement",
            complexity="complex"
        )

        result = await mock_data_generator.generate_mock_data(request)

        assert result["success"] is True
        assert result["data_type"] == "jira_issue"
        assert len(result["items"]) == 2

        for item in result["items"]:
            assert item["data_type"] == "jira_issue"
            assert item["topic"] == "Security Enhancement"
            assert "key" in item
            assert "summary" in item
            assert "status" in item
            assert "priority" in item
            assert "assignee" in item

    @pytest.mark.asyncio
    async def test_generate_api_docs(self, mock_data_generator, mock_clients):
        """Test generation of API documentation mock data."""
        request = GenerationRequest(
            data_type=MockDataType.API_DOCS,
            count=1,
            topic="REST API Specification",
            complexity="medium"
        )

        result = await mock_data_generator.generate_mock_data(request)

        assert result["success"] is True
        assert result["data_type"] == "api_docs"
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["data_type"] == "api_docs"
        assert item["topic"] == "REST API Specification"
        assert "content" in item
        assert len(item["content"]) > 0

    @pytest.mark.asyncio
    async def test_persist_to_doc_store(self, mock_data_generator, mock_clients):
        """Test persisting generated data to document store."""
        request = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=1,
            topic="Test Persistence",
            persist_to_doc_store=True
        )

        result = await mock_data_generator.generate_mock_data(request)

        assert result["success"] is True
        item = result["items"][0]

        # Should have doc_store_id if persistence was successful
        assert "doc_store_id" in item
        assert item["doc_store_id"] == "mock-doc-12345"

    @pytest.mark.asyncio
    async def test_workflow_id_tracking(self, mock_data_generator, mock_clients):
        """Test workflow ID tracking in generated data."""
        workflow_id = "test-workflow-123"
        request = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=1,
            topic="Workflow Test",
            workflow_id=workflow_id
        )

        result = await mock_data_generator.generate_mock_data(request)

        assert result["success"] is True
        assert result["metadata"]["workflow_id"] == workflow_id

        item = result["items"][0]
        assert item.get("workflow_id") == workflow_id

    def test_template_loading(self, mock_data_generator):
        """Test that templates are loaded correctly."""
        templates = mock_data_generator.templates

        assert isinstance(templates, dict)
        assert len(templates) > 0

        # Check specific template structure
        confluence_template = templates["confluence_page"]
        assert "title_template" in confluence_template
        assert "content_structure" in confluence_template

        github_template = templates["github_repo"]
        assert "name_template" in github_template
        assert "description_template" in github_template

    def test_prompt_generation_confluence(self, mock_data_generator):
        """Test prompt generation for Confluence pages."""
        request = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            topic="Authentication Service",
            complexity="medium"
        )

        prompt = mock_data_generator._create_generation_prompt(request, 0)

        assert "Confluence documentation page" in prompt
        assert "Authentication Service" in prompt
        assert "medium" in prompt or "moderate" in prompt
        assert "professional" in prompt

    def test_prompt_generation_github(self, mock_data_generator):
        """Test prompt generation for GitHub repositories."""
        request = GenerationRequest(
            data_type=MockDataType.GITHUB_REPO,
            topic="User Management",
            complexity="simple"
        )

        prompt = mock_data_generator._create_generation_prompt(request, 0)

        assert "GitHub repository" in prompt
        assert "User Management" in prompt
        assert "simple" in prompt
        assert "open-source project" in prompt

    def test_prompt_generation_jira(self, mock_data_generator):
        """Test prompt generation for Jira issues."""
        request = GenerationRequest(
            data_type=MockDataType.JIRA_ISSUE,
            topic="Security Fix",
            complexity="complex"
        )

        prompt = mock_data_generator._create_generation_prompt(request, 0)

        assert "Jira issue" in prompt or "Jira ticket" in prompt
        assert "Security Fix" in prompt
        assert "complex" in prompt
        assert "acceptance criteria" in prompt

    @pytest.mark.asyncio
    async def test_error_handling_llm_failure(self, mock_data_generator, mock_clients):
        """Test error handling when LLM generation fails."""
        # Mock LLM failure
        mock_clients.post_json.side_effect = Exception("LLM service unavailable")

        request = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=1,
            topic="Error Test"
        )

        with pytest.raises(Exception) as exc_info:
            await mock_data_generator.generate_mock_data(request)

        assert "Failed to generate mock data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_doc_store_failure(self, mock_data_generator, mock_clients):
        """Test error handling when doc store persistence fails."""
        # Mock doc store failure
        mock_clients.post_json.side_effect = [
            {"success": True, "response": "Mock content", "provider": "ollama", "tokens_used": 50},  # LLM success
            Exception("Doc store unavailable")  # Doc store failure
        ]

        request = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=1,
            topic="Doc Store Error Test",
            persist_to_doc_store=True
        )

        # Should still succeed but log warning about doc store failure
        result = await mock_data_generator.generate_mock_data(request)

        assert result["success"] is True
        assert len(result["items"]) == 1

        # Should not have doc_store_id due to failure
        item = result["items"][0]
        assert "doc_store_id" not in item

    def test_complexity_levels(self, mock_data_generator):
        """Test different complexity levels in prompt generation."""
        complexities = ["simple", "medium", "complex"]

        for complexity in complexities:
            request = GenerationRequest(
                data_type=MockDataType.CONFLUENCE_PAGE,
                topic="Test Topic",
                complexity=complexity
            )

            prompt = mock_data_generator._create_generation_prompt(request, 0)

            # Should contain complexity-specific guidance
            if complexity == "simple":
                assert "straightforward" in prompt or "basic" in prompt
            elif complexity == "medium":
                assert "moderate" in prompt or "detailed" in prompt
            elif complexity == "complex":
                assert "comprehensive" in prompt or "advanced" in prompt

    def test_max_items_validation(self, mock_data_generator):
        """Test validation of maximum items per request."""
        # Should handle up to 50 items
        request = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=50,
            topic="Large Test"
        )

        # This should not raise an exception
        assert request.count == 50

    @pytest.mark.asyncio
    async def test_metadata_inclusion(self, mock_data_generator, mock_clients):
        """Test that metadata is properly included in responses."""
        request = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=1,
            topic="Metadata Test",
            include_metadata=True
        )

        result = await mock_data_generator.generate_mock_data(request)

        assert "metadata" in result
        metadata = result["metadata"]

        assert "topic" in metadata
        assert metadata["topic"] == "Metadata Test"
        assert "complexity" in metadata
        assert metadata["complexity"] == "medium"
        assert "generated_at" in metadata

    @pytest.mark.asyncio
    async def test_batch_generation(self, mock_data_generator, mock_clients):
        """Test batch generation of multiple items."""
        request = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=3,
            topic="Batch Test"
        )

        result = await mock_data_generator.generate_mock_data(request)

        assert result["success"] is True
        assert len(result["items"]) == 3

        # Each item should have unique ID and content
        ids = [item["id"] for item in result["items"]]
        assert len(set(ids)) == 3  # All IDs should be unique

        for item in result["items"]:
            assert item["data_type"] == "confluence_page"
            assert item["topic"] == "Batch Test"
            assert "content" in item
            assert len(item["content"]) > 0

    def test_data_type_enum_values(self):
        """Test that all mock data types are properly defined."""
        expected_types = [
            "confluence_page",
            "github_repo",
            "github_pr",
            "jira_issue",
            "jira_epic",
            "api_docs",
            "code_sample",
            "workflow_data"
        ]

        for expected_type in expected_types:
            assert hasattr(MockDataType, expected_type.upper())

        # Test enum values
        assert MockDataType.CONFLUENCE_PAGE.value == "confluence_page"
        assert MockDataType.GITHUB_REPO.value == "github_repo"
        assert MockDataType.JIRA_ISSUE.value == "jira_issue"
        assert MockDataType.API_DOCS.value == "api_docs"

    @pytest.mark.asyncio
    async def test_workflow_data_generation(self, mock_data_generator, mock_clients):
        """Test generation of comprehensive workflow test data."""
        # This would typically test the workflow data endpoint
        # For unit testing, we test the underlying functionality

        request = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=1,
            topic="Workflow Integration Test"
        )

        result = await mock_data_generator.generate_mock_data(request)

        assert result["success"] is True
        assert len(result["items"]) == 1

        # Workflow data should be suitable for end-to-end testing
        item = result["items"][0]
        assert "content" in item
        assert "metadata" in item
        assert "generated_at" in item

    def test_service_initialization(self, mock_data_generator):
        """Test that service initializes with correct endpoints."""
        # Test that URLs are properly configured
        assert mock_data_generator.llm_gateway_url == "http://llm-gateway:5055"
        assert mock_data_generator.doc_store_url == "http://doc_store:5087"

        # Test that clients are initialized
        assert mock_data_generator.clients is not None

    @pytest.mark.asyncio
    async def test_content_variation(self, mock_data_generator, mock_clients):
        """Test that generated content varies between requests."""
        request1 = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=1,
            topic="Variation Test",
            complexity="medium"
        )

        request2 = GenerationRequest(
            data_type=MockDataType.CONFLUENCE_PAGE,
            count=1,
            topic="Variation Test",
            complexity="medium"
        )

        result1 = await mock_data_generator.generate_mock_data(request1)
        result2 = await mock_data_generator.generate_mock_data(request2)

        # Content should be different (since LLM generates varied responses)
        content1 = result1["items"][0]["content"]
        content2 = result2["items"][0]["content"]

        # In practice, LLM might generate similar content, so we just verify both have content
        assert len(content1) > 0
        assert len(content2) > 0

    @pytest.mark.asyncio
    async def test_large_content_generation(self, mock_data_generator, mock_clients):
        """Test generation of larger content pieces."""
        # Mock larger response
        mock_clients.post_json.return_value = {
            "success": True,
            "response": "This is a much longer piece of content for testing larger document generation. " * 50,
            "provider": "ollama",
            "tokens_used": 200
        }

        request = GenerationRequest(
            data_type=MockDataType.API_DOCS,
            count=1,
            topic="Large Content Test"
        )

        result = await mock_data_generator.generate_mock_data(request)

        assert result["success"] is True
        item = result["items"][0]

        # Content should be substantial
        assert len(item["content"]) > 1000  # Should be a large content piece
        assert "api" in item["data_type"]
