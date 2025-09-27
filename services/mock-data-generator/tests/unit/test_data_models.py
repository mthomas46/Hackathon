"""Unit tests for mock-data-generator data models."""

import pytest
from datetime import datetime
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


class BulkCollectionRequest(BaseModel):
    """Request model for bulk collection generation."""
    name: str = Field(..., description="Name of the collection")
    data_types: List[str] = Field(..., description="Types of data to include")
    total_items: int = Field(default=5, ge=1, le=1000, description="Total number of items to generate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")


class BulkCollectionResponse(BaseModel):
    """Response model for bulk collection generation."""
    collection_id: str = Field(..., description="Unique identifier for the collection")
    name: str = Field(..., description="Name of the collection")
    total_items: int = Field(..., description="Total number of items requested")
    generated_items: int = Field(..., description="Number of items actually generated")
    data_types: List[str] = Field(..., description="Types of data generated")
    status: str = Field(..., description="Status of the generation process")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="Generated items")


class EcosystemScenarioRequest(BaseModel):
    """Request model for ecosystem scenario generation."""
    scenario_type: str = Field(..., description="Type of scenario to generate")
    scale: str = Field(default="small", description="Scale of the scenario (small, medium, large)")
    include_services: List[str] = Field(default_factory=list, description="Services to include in scenario")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")


class EcosystemScenarioResponse(BaseModel):
    """Response model for ecosystem scenario generation."""
    scenario_id: str = Field(..., description="Unique identifier for the scenario")
    scenario_type: str = Field(..., description="Type of scenario generated")
    scale: str = Field(..., description="Scale of the scenario")
    total_items: int = Field(..., description="Total number of items in scenario")
    generated_items: int = Field(..., description="Number of items actually generated")
    collections: List[str] = Field(default_factory=list, description="Collections created")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TestMockDataType:
    """Test the MockDataType enum."""

    def test_enum_values(self):
        """Test that all expected enum values exist."""
        assert MockDataType.CONFLUENCE_PAGE == "confluence_page"
        assert MockDataType.GITHUB_REPO == "github_repo"
        assert MockDataType.GITHUB_PR == "github_pr"
        assert MockDataType.JIRA_TICKET == "jira_ticket"
        assert MockDataType.JIRA_EPIC == "jira_epic"
        assert MockDataType.PROJECT_DOC == "project_doc"
        assert MockDataType.API_DOC == "api_doc"

    def test_enum_membership(self):
        """Test that values are valid enum members."""
        assert "confluence_page" in [e.value for e in MockDataType]
        assert "github_repo" in [e.value for e in MockDataType]
        assert "github_pr" in [e.value for e in MockDataType]
        assert "jira_ticket" in [e.value for e in MockDataType]


class TestGenerationRequest:
    """Test the GenerationRequest model."""

    def test_valid_request(self):
        """Test creating a valid generation request."""
        request = GenerationRequest(
            data_type="confluence_page",
            count=5,
            parameters={"title": "Test Page", "space": "TEST"}
        )

        assert request.data_type == "confluence_page"
        assert request.count == 5
        assert request.parameters == {"title": "Test Page", "space": "TEST"}

    def test_default_values(self):
        """Test default values in generation request."""
        request = GenerationRequest(data_type="github_repo")

        assert request.data_type == "github_repo"
        assert request.count == 1
        assert request.parameters == {}

    def test_data_type_string(self):
        """Test that data_type accepts any string (validation happens elsewhere)."""
        request = GenerationRequest(data_type="any_string_works")
        assert request.data_type == "any_string_works"


class TestMockDataResponse:
    """Test the MockDataResponse model."""

    def test_valid_response(self):
        """Test creating a valid mock data response."""
        response = MockDataResponse(
            success=True,
            data=[{"id": "test1", "content": "Test content"}],
            count=1,
            data_type="confluence_page",
            metadata={"generated_at": "2024-01-01"}
        )

        assert response.success is True
        assert len(response.data) == 1
        assert response.count == 1
        assert response.data_type == "confluence_page"
        assert response.metadata == {"generated_at": "2024-01-01"}

    def test_default_values(self):
        """Test default values in response."""
        response = MockDataResponse(success=True, data=[], count=0)

        assert response.success is True
        assert response.data == []
        assert response.count == 0
        assert response.data_type is None
        assert response.metadata == {}
        assert response.error_message == ""


class TestBulkCollectionRequest:
    """Test the BulkCollectionRequest model."""

    def test_valid_request(self):
        """Test creating a valid bulk collection request."""
        request = BulkCollectionRequest(
            name="test_collection",
            data_types=["confluence_page", "github_repo"],
            total_items=10,
            parameters={"space": "TEST", "org": "testorg"}
        )

        assert request.name == "test_collection"
        assert request.data_types == ["confluence_page", "github_repo"]
        assert request.total_items == 10
        assert request.parameters == {"space": "TEST", "org": "testorg"}

    def test_default_values(self):
        """Test default values in bulk collection request."""
        request = BulkCollectionRequest(
            name="test",
            data_types=["confluence_page"]
        )

        assert request.name == "test"
        assert request.data_types == ["confluence_page"]
        assert request.total_items == 5
        assert request.parameters == {}


class TestBulkCollectionResponse:
    """Test the BulkCollectionResponse model."""

    def test_valid_response(self):
        """Test creating a valid bulk collection response."""
        response = BulkCollectionResponse(
            collection_id="coll_123",
            name="test_collection",
            total_items=10,
            generated_items=8,
            data_types=["confluence_page", "github_repo"],
            status="completed",
            items=[{"id": "item1"}, {"id": "item2"}]
        )

        assert response.collection_id == "coll_123"
        assert response.name == "test_collection"
        assert response.total_items == 10
        assert response.generated_items == 8
        assert response.data_types == ["confluence_page", "github_repo"]
        assert response.status == "completed"
        assert len(response.items) == 2

    def test_default_values(self):
        """Test default values in bulk collection response."""
        response = BulkCollectionResponse(
            collection_id="coll_123",
            name="test",
            total_items=5,
            generated_items=5,
            data_types=["confluence_page"],
            status="completed"
        )

        assert response.collection_id == "coll_123"
        assert response.name == "test"
        assert response.total_items == 5
        assert response.generated_items == 5
        assert response.data_types == ["confluence_page"]
        assert response.status == "completed"
        assert response.items == []


class TestEcosystemScenarioRequest:
    """Test the EcosystemScenarioRequest model."""

    def test_valid_request(self):
        """Test creating a valid ecosystem scenario request."""
        request = EcosystemScenarioRequest(
            scenario_type="full_ecosystem",
            scale="medium",
            include_services=["llm-gateway", "doc-store"],
            parameters={"user_count": 10, "project_count": 5}
        )

        assert request.scenario_type == "full_ecosystem"
        assert request.scale == "medium"
        assert request.include_services == ["llm-gateway", "doc-store"]
        assert request.parameters == {"user_count": 10, "project_count": 5}

    def test_default_values(self):
        """Test default values in ecosystem scenario request."""
        request = EcosystemScenarioRequest(scenario_type="basic")

        assert request.scenario_type == "basic"
        assert request.scale == "small"
        assert request.include_services == []
        assert request.parameters == {}


class TestEcosystemScenarioResponse:
    """Test the EcosystemScenarioResponse model."""

    def test_valid_response(self):
        """Test creating a valid ecosystem scenario response."""
        response = EcosystemScenarioResponse(
            scenario_id="scenario_123",
            scenario_type="full_ecosystem",
            scale="medium",
            total_items=50,
            generated_items=45,
            collections=["users", "projects", "documents"],
            metadata={"duration_seconds": 30.5}
        )

        assert response.scenario_id == "scenario_123"
        assert response.scenario_type == "full_ecosystem"
        assert response.scale == "medium"
        assert response.total_items == 50
        assert response.generated_items == 45
        assert response.collections == ["users", "projects", "documents"]
        assert response.metadata == {"duration_seconds": 30.5}

    def test_default_values(self):
        """Test default values in ecosystem scenario response."""
        response = EcosystemScenarioResponse(
            scenario_id="scenario_123",
            scenario_type="basic",
            scale="small",
            total_items=10,
            generated_items=10
        )

        assert response.scenario_id == "scenario_123"
        assert response.scenario_type == "basic"
        assert response.scale == "small"
        assert response.total_items == 10
        assert response.generated_items == 10
        assert response.collections == []
        assert response.metadata == {}


def test_data_type_enum_values():
    """Test that MockDataType enum has expected values."""
    expected_values = [
        "confluence_page", "github_repo", "github_pr",
        "jira_ticket", "jira_epic", "project_doc", "api_doc"
    ]

    for value in expected_values:
        assert value in [e.value for e in MockDataType]
