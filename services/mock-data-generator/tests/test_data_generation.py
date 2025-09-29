"""Tests for mock data generation business logic."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from ..main import (
    MockDataGenerator,
    MockDataType,
    generate_confluence_page,
    generate_github_repo,
    generate_jira_ticket,
    generate_bulk_collection,
    generate_ecosystem_scenario,
)


class TestMockDataGenerator:
    """Test the MockDataGenerator class."""

    def test_initialization(self):
        """Test MockDataGenerator initialization."""
        generator = MockDataGenerator()
        assert generator.llm_gateway_url is not None
        assert generator.doc_store_url is not None

    @patch('httpx.AsyncClient')
    def test_generate_single_item(self, mock_client):
        """Test generating a single mock data item."""
        # Mock LLM Gateway response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Mock generated content"
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        generator = MockDataGenerator()
        result = generator.generate_mock_data("confluence_page", 1, {"title": "Test"})

        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["count"] == 1
        assert result["data_type"] == "confluence_page"

    @patch('httpx.AsyncClient')
    def test_generate_multiple_items(self, mock_client):
        """Test generating multiple mock data items."""
        # Mock LLM Gateway response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Mock generated content for item {i}"
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        generator = MockDataGenerator()
        result = generator.generate_mock_data("github_repo", 3, {"owner": "testuser"})

        assert result["success"] is True
        assert len(result["data"]) == 3
        assert result["count"] == 3
        assert result["data_type"] == "github_repo"

    def test_generate_invalid_data_type(self):
        """Test generating with invalid data type."""
        generator = MockDataGenerator()

        with pytest.raises(ValueError, match="Unsupported data type"):
            generator.generate_mock_data("invalid_type", 1, {})

    def test_generate_count_exceeds_limit(self):
        """Test generating with count exceeding limit."""
        generator = MockDataGenerator()

        with pytest.raises(ValueError, match="Count must be between 1 and 100"):
            generator.generate_mock_data("confluence_page", 150, {})

    def test_generate_zero_count(self):
        """Test generating with zero count."""
        generator = MockDataGenerator()

        with pytest.raises(ValueError, match="Count must be between 1 and 100"):
            generator.generate_mock_data("confluence_page", 0, {})


class TestConfluencePageGeneration:
    """Test Confluence page generation."""

    @patch('httpx.AsyncClient')
    def test_generate_confluence_page_basic(self, mock_client):
        """Test basic Confluence page generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "This is a comprehensive API documentation page."
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = generate_confluence_page({"title": "API Docs", "space": "DEV"})

        assert "id" in result
        assert result["type"] == "confluence_page"
        assert "title" in result
        assert "content" in result
        assert "space" in result
        assert "created_date" in result
        assert "last_modified" in result
        assert "version" in result

    @patch('httpx.AsyncClient')
    def test_generate_confluence_page_with_labels(self, mock_client):
        """Test Confluence page generation with labels."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Technical documentation content."
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = generate_confluence_page({
            "title": "Tech Docs",
            "space": "TECH",
            "labels": ["documentation", "api"]
        })

        assert result["labels"] == ["documentation", "api"]
        assert "content" in result


class TestGitHubRepoGeneration:
    """Test GitHub repository generation."""

    @patch('httpx.AsyncClient')
    def test_generate_github_repo_basic(self, mock_client):
        """Test basic GitHub repository generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "# Test Repository\n\nThis is a test repository."
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = generate_github_repo({"name": "test-repo", "owner": "testuser"})

        assert "id" in result
        assert result["type"] == "github_repo"
        assert result["name"] == "test-repo"
        assert result["owner"] == "testuser"
        assert "description" in result
        assert "readme_content" in result
        assert "language" in result
        assert "stars" in result
        assert "forks" in result

    @patch('httpx.AsyncClient')
    def test_generate_github_repo_with_topics(self, mock_client):
        """Test GitHub repo generation with topics."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Repository for testing purposes."
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = generate_github_repo({
            "name": "test-repo",
            "owner": "testuser",
            "topics": ["testing", "python", "automation"]
        })

        assert result["topics"] == ["testing", "python", "automation"]


class TestJiraTicketGeneration:
    """Test Jira ticket generation."""

    @patch('httpx.AsyncClient')
    def test_generate_jira_ticket_basic(self, mock_client):
        """Test basic Jira ticket generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "As a user, I need to implement login functionality."
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = generate_jira_ticket({
            "project": "PROJ",
            "issue_type": "Story",
            "priority": "Medium"
        })

        assert "id" in result
        assert result["type"] == "jira_ticket"
        assert "key" in result
        assert "summary" in result
        assert "description" in result
        assert "status" in result
        assert "priority" in result
        assert "assignee" in result
        assert "reporter" in result

    @patch('httpx.AsyncClient')
    def test_generate_jira_ticket_with_epic_link(self, mock_client):
        """Test Jira ticket generation with epic link."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Implement user authentication feature."
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = generate_jira_ticket({
            "project": "PROJ",
            "issue_type": "Story",
            "epic_link": "PROJ-123"
        })

        assert result["epic_link"] == "PROJ-123"


class TestBulkCollectionGeneration:
    """Test bulk collection generation."""

    @patch('httpx.AsyncClient')
    def test_generate_bulk_collection(self, mock_client):
        """Test bulk collection generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Bulk collection content"
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = generate_bulk_collection({
            "name": "test_collection",
            "data_types": ["confluence_page", "github_repo"],
            "total_items": 5
        })

        assert result["success"] is True
        assert "collection_id" in result
        assert result["name"] == "test_collection"
        assert result["total_items"] == 5
        assert "generated_items" in result
        assert "items" in result

    def test_generate_bulk_collection_invalid_types(self):
        """Test bulk collection with invalid data types."""
        with pytest.raises(ValueError, match="Unsupported data type"):
            generate_bulk_collection({
                "name": "test",
                "data_types": ["invalid_type"],
                "total_items": 3
            })


class TestEcosystemScenarioGeneration:
    """Test ecosystem scenario generation."""

    @patch('httpx.AsyncClient')
    def test_generate_ecosystem_scenario(self, mock_client):
        """Test ecosystem scenario generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Ecosystem scenario content"
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = generate_ecosystem_scenario({
            "scenario_type": "development_environment",
            "scale": "small",
            "include_services": ["llm-gateway", "doc-store"]
        })

        assert result["success"] is True
        assert "scenario_id" in result
        assert result["scenario_type"] == "development_environment"
        assert result["scale"] == "small"
        assert "total_items" in result
        assert "collections" in result

    def test_generate_ecosystem_scenario_invalid_scale(self):
        """Test ecosystem scenario with invalid scale."""
        with pytest.raises(ValueError, match="Invalid scale"):
            generate_ecosystem_scenario({
                "scenario_type": "development_environment",
                "scale": "invalid_scale"
            })


class TestDataValidation:
    """Test data validation functions."""

    def test_validate_data_type_valid(self):
        """Test validating valid data types."""
        from ..main import validate_data_type

        # Should not raise exception
        validate_data_type("confluence_page")
        validate_data_type("github_repo")
        validate_data_type("jira_ticket")

    def test_validate_data_type_invalid(self):
        """Test validating invalid data types."""
        from ..main import validate_data_type

        with pytest.raises(ValueError, match="Unsupported data type"):
            validate_data_type("invalid_type")

    def test_validate_generation_params_valid(self):
        """Test validating valid generation parameters."""
        from ..main import validate_generation_params

        # Should not raise exception
        validate_generation_params("confluence_page", 5, {"title": "Test"})

    def test_validate_generation_params_invalid_count(self):
        """Test validating invalid count parameter."""
        from ..main import validate_generation_params

        with pytest.raises(ValueError, match="Count must be between 1 and 100"):
            validate_generation_params("confluence_page", 150, {})

    def test_validate_generation_params_invalid_type(self):
        """Test validating with invalid data type."""
        from ..main import validate_generation_params

        with pytest.raises(ValueError, match="Unsupported data type"):
            validate_generation_params("invalid_type", 5, {})


class TestIntegrationWithDocStore:
    """Test integration with document store."""

    @patch('httpx.AsyncClient')
    def test_store_generated_data(self, mock_client):
        """Test storing generated data in doc store."""
        # Mock doc store response
        mock_store_response = MagicMock()
        mock_store_response.status_code = 201
        mock_store_response.json.return_value = {"id": "stored_doc_123"}

        # Mock LLM Gateway response
        mock_llm_response = MagicMock()
        mock_llm_response.json.return_value = {"content": "Generated content"}

        def mock_post(url, **kwargs):
            if "doc_store" in url:
                return mock_store_response
            else:
                return mock_llm_response

        mock_client.return_value.__aenter__.return_value.post.side_effect = mock_post

        generator = MockDataGenerator()
        result = generator.generate_and_store("confluence_page", 1, {"title": "Test"})

        assert result["success"] is True
        assert "stored_ids" in result
        assert len(result["stored_ids"]) == 1
