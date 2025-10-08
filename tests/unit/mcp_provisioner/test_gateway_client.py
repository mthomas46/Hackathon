"""
Unit tests for GatewayClient.

TDD GREEN Phase: Tests should pass now that Gateway Client is implemented.
"""

import pytest
import httpx
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, Mock

# Add mcp-provisioner service root to path
service_root = Path(__file__).parent.parent.parent.parent / "services" / "mcp-provisioner"
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

# Import using the Docker/service internal structure
from infrastructure.external_services.gateway_client import GatewayClient


@pytest.mark.asyncio
class TestGatewayClient:
    """Unit tests for GatewayClient."""
    
    async def test_gateway_client_init(self):
        """Test GatewayClient initialization."""
        client = GatewayClient(gateway_url="http://test-gateway:8001")
        
        assert client.gateway_url == "http://test-gateway:8001"
        assert client.client is not None
    
    @patch('httpx.AsyncClient.post')
    async def test_register_mcp_success(self, mock_post):
        """Test successful MCP registration with gateway."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "instance-123", "mcp_id": "test-mcp"}
        mock_post.return_value = mock_response
        
        client = GatewayClient(gateway_url="http://test-gateway:8001")
        
        # Act
        result = await client.register_mcp(
            mcp_id="test-mcp",
            host="localhost",
            port=54321,
            name="Test MCP",
            tier=2,
            health_check_url="http://localhost:54321/health",
            tags=["test", "tier-2"],
            metadata={"version": "1.0"}
        )
        
        # Assert
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://test-gateway:8001/api/v1/gateway/register"
        
        payload = call_args[1]['json']
        assert payload['mcp_id'] == "test-mcp"
        assert payload['host'] == "localhost"
        assert payload['port'] == 54321
        assert payload['tier'] == 2
    
    @patch('httpx.AsyncClient.post')
    async def test_register_mcp_failure(self, mock_post):
        """Test MCP registration failure handling."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        client = GatewayClient()
        
        # Act
        result = await client.register_mcp(
            mcp_id="test-mcp",
            host="localhost",
            port=54321,
            name="Test MCP",
            tier=2,
            health_check_url="http://localhost:54321/health"
        )
        
        # Assert
        assert result is False
    
    @patch('httpx.AsyncClient.post')
    async def test_register_mcp_exception(self, mock_post):
        """Test MCP registration with network exception."""
        # Arrange
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        client = GatewayClient()
        
        # Act
        result = await client.register_mcp(
            mcp_id="test-mcp",
            host="localhost",
            port=54321,
            name="Test MCP",
            tier=2,
            health_check_url="http://localhost:54321/health"
        )
        
        # Assert
        assert result is False
    
    async def test_gateway_client_close(self):
        """Test GatewayClient cleanup."""
        client = GatewayClient()
        
        # Should not raise exception
        await client.close()
        
        # Client should be closed
        assert client.client.is_closed

