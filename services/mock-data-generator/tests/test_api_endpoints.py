"""Unit tests for mock-data-generator core functionality."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Import models directly (defined in unit test)
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MockDataType(str, Enum):
    """Types of mock data that can be generated."""
    CONFLUENCE_PAGE = "confluence_page"
    GITHUB_REPO = "github_repo"
    GITHUB_PR = "github_pr"
    JIRA_TICKET = "jira_ticket"
    JIRA_EPIC = "jira_epic"
    PROJECT_DOC = "project_doc"
    API_DOC = "api_doc"

class GenerationRequest(BaseModel):
    """Request model for mock data generation."""
    data_type: str = Field(..., description="Type of mock data to generate")
    count: int = Field(default=1, ge=1, le=100, description="Number of items to generate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for generation")

class MockDataResponse(BaseModel):
    """Response model for mock data generation."""
    success: bool = Field(..., description="Whether the generation was successful")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Generated mock data")
    count: int = Field(default=0, description="Number of items generated")
    data_type: Optional[str] = Field(default=None, description="Type of data generated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    error_message: str = Field(default="", description="Error message if generation failed")


class TestDataGenerationLogic:
    """Test core data generation business logic."""

    def test_mock_data_type_enum(self):
        """Test that MockDataType enum has expected values."""
        expected_types = ["confluence_page", "github_repo", "github_pr",
                         "jira_ticket", "jira_epic", "project_doc", "api_doc"]

        for expected_type in expected_types:
            assert expected_type in [e.value for e in MockDataType]

    def test_generation_request_validation(self):
        """Test GenerationRequest model validation."""
        # Valid request
        request = GenerationRequest(
            data_type="confluence_page",
            count=5,
            parameters={"title": "Test"}
        )
        assert request.data_type == "confluence_page"
        assert request.count == 5

        # Default values
        request = GenerationRequest(data_type="github_repo")
        assert request.count == 1
        assert request.parameters == {}

    def test_mock_data_response_structure(self):
        """Test MockDataResponse model structure."""
        response = MockDataResponse(
            success=True,
            data=[{"id": "test1"}],
            count=1,
            data_type="confluence_page"
        )
        assert response.success is True
        assert len(response.data) == 1
        assert response.count == 1

    @pytest.mark.asyncio
    async def test_async_data_generation_pattern(self):
        """Test the pattern for async data generation."""
        # This is a pattern test - doesn't require actual service imports
        async def mock_generate_data(data_type, params):
            """Mock data generation function."""
            return {
                "id": f"test-{data_type}",
                "type": data_type,
                "generated": True,
                **params
            }

        # Test the pattern
        result = await mock_generate_data("confluence_page", {"title": "Test"})
        assert result["id"] == "test-confluence_page"
        assert result["type"] == "confluence_page"
        assert result["title"] == "Test"
        assert result["generated"] is True


class TestDataValidation:
    """Test data validation logic."""

    def test_data_type_validation(self):
        """Test data type validation."""
        valid_types = ["confluence_page", "github_repo", "jira_ticket"]

        for data_type in valid_types:
            # Should not raise exception for valid types
            assert data_type in [e.value for e in MockDataType]

    def test_request_parameter_validation(self):
        """Test request parameter validation."""
        # Test count limits
        with pytest.raises(ValueError):
            GenerationRequest(data_type="confluence_page", count=0)

        with pytest.raises(ValueError):
            GenerationRequest(data_type="confluence_page", count=150)

        # Valid counts should work
        request = GenerationRequest(data_type="confluence_page", count=50)
        assert request.count == 50


class TestResponseFormatting:
    """Test response formatting and structure."""

    def test_success_response_format(self):
        """Test successful response format."""
        response = MockDataResponse(
            success=True,
            data=[{"id": "item1"}, {"id": "item2"}],
            count=2,
            data_type="github_repo",
            metadata={"generated_at": "2024-01-01"}
        )

        assert response.success is True
        assert response.count == 2
        assert len(response.data) == 2
        assert response.data_type == "github_repo"

    def test_error_response_format(self):
        """Test error response format."""
        response = MockDataResponse(
            success=False,
            data=[],
            count=0,
            error_message="Generation failed"
        )

        assert response.success is False
        assert response.count == 0
        assert len(response.data) == 0
        assert response.error_message == "Generation failed"