"""Unit tests for Provision MCP Use Case."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from services.mcp_provisioner.application.use_cases.provision_mcp_use_case import ProvisionMCPUseCase
from services.mcp_provisioner.application.dto.provision_request_dto import ProvisionRequestDTO
from services.mcp_provisioner.domain.entities.mcp_instance import MCPInstance
from services.mcp_provisioner.domain.value_objects.mcp_state import MCPState


@pytest.fixture
def mock_repository():
    """Mock MCP repository."""
    repository = AsyncMock()
    repository.save = AsyncMock()
    return repository


@pytest.fixture
def provision_use_case(mock_repository):
    """Create provision use case with mocked repository."""
    return ProvisionMCPUseCase(repository=mock_repository)


@pytest.fixture
def valid_provision_request():
    """Valid provision request."""
    return ProvisionRequestDTO(
        client_id="client-123",
        tier=0,
        memory_limit="512m",
        cpu_shares=1024,
        metadata={"owner": "team-a"}
    )


@pytest.mark.asyncio
async def test_provision_success(provision_use_case, mock_repository, valid_provision_request):
    """Test successful provisioning."""
    # Act
    result = await provision_use_case.execute(valid_provision_request)
    
    # Assert
    assert result.is_success()
    assert result.message.startswith("MCP instance provisioned successfully")
    assert result.data is not None
    assert result.data.client_id == "client-123"
    assert result.data.state == "cold"
    assert result.data.tier == 0
    
    # Verify repository was called
    mock_repository.save.assert_called_once()


@pytest.mark.asyncio
async def test_provision_with_custom_image(provision_use_case, mock_repository):
    """Test provisioning with custom image."""
    request = ProvisionRequestDTO(
        client_id="client-456",
        tier=1,
        image_name="custom-mcp:v2.0",
    )
    
    result = await provision_use_case.execute(request)
    
    assert result.is_success()
    assert result.data.image_name == "custom-mcp:v2.0"


@pytest.mark.asyncio
async def test_provision_invalid_tier(provision_use_case, mock_repository):
    """Test provisioning with invalid tier."""
    with pytest.raises(ValueError, match="tier must be an integer between 0 and 4"):
        ProvisionRequestDTO(
            client_id="client-789",
            tier=5,  # Invalid tier
        )


@pytest.mark.asyncio
async def test_provision_empty_client_id(provision_use_case, mock_repository):
    """Test provisioning with empty client_id."""
    with pytest.raises(ValueError, match="client_id is required"):
        ProvisionRequestDTO(
            client_id="",
            tier=0,
        )


@pytest.mark.asyncio
async def test_provision_repository_error(provision_use_case, mock_repository):
    """Test handling of repository errors."""
    mock_repository.save.side_effect = Exception("Database error")
    
    request = ProvisionRequestDTO(
        client_id="client-999",
        tier=0,
    )
    
    result = await provision_use_case.execute(request)
    
    assert result.is_failure()
    assert "Failed to provision MCP instance" in result.message
    assert len(result.errors) > 0

