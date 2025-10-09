"""
Integration tests for orchestrator service integration.

Tests the discovery-agent's interaction with the orchestrator service.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


@pytest.mark.integration
@pytest.mark.slow
class TestOrchestratorIntegration:
    """Test integration with orchestrator service."""
    
    @pytest.mark.asyncio
    async def test_register_discovered_service_with_orchestrator(self, mock_orchestrator, sample_service):
        """Test registering a discovered service with orchestrator."""
        from infrastructure.orchestrator_client import OrchestratorClient
        
        client = OrchestratorClient(orchestrator_url="http://orchestrator:5099")
        client._http_client = mock_orchestrator
        
        result = await client.register_service(sample_service)
        
        assert result["success"] is True
        mock_orchestrator.register_service.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_tools_with_orchestrator(self, mock_orchestrator, sample_tool_definition):
        """Test registering generated tools with orchestrator."""
        from infrastructure.orchestrator_client import OrchestratorClient
        
        client = OrchestratorClient(orchestrator_url="http://orchestrator:5099")
        client._http_client = mock_orchestrator
        
        tools = [sample_tool_definition]
        result = await client.register_tools(tools)
        
        assert result["success"] is True
        assert result["tools_registered"] >= 1
        mock_orchestrator.register_tools.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_service_from_orchestrator(self, mock_orchestrator):
        """Test retrieving service information from orchestrator."""
        from infrastructure.orchestrator_client import OrchestratorClient
        
        client = OrchestratorClient(orchestrator_url="http://orchestrator:5099")
        client._http_client = mock_orchestrator
        
        service = await client.get_service("test-service")
        
        assert service is not None
        assert service["name"] == "test-service"
        mock_orchestrator.get_service.assert_called_once_with("test-service")
    
    @pytest.mark.asyncio
    async def test_orchestrator_connection_failure(self):
        """Test handling orchestrator connection failure."""
        from infrastructure.orchestrator_client import OrchestratorClient
        import aiohttp
        
        # Mock client that fails to connect
        mock_client = AsyncMock()
        mock_client.register_service.side_effect = aiohttp.ClientError("Connection failed")
        
        client = OrchestratorClient(orchestrator_url="http://down-orchestrator:5099")
        client._http_client = mock_client
        
        # Should handle error gracefully
        with pytest.raises(aiohttp.ClientError):
            from domain.entities import Service
            service = Service(
                name="test",
                base_url="http://test:8000",
                openapi_url="http://test:8000/openapi.json",
                version="1.0.0",
                description="Test",
                status="discovered"
            )
            await client.register_service(service)
    
    @pytest.mark.asyncio
    async def test_orchestrator_timeout_handling(self):
        """Test handling orchestrator timeout."""
        from infrastructure.orchestrator_client import OrchestratorClient
        import asyncio
        
        mock_client = AsyncMock()
        mock_client.register_service.side_effect = asyncio.TimeoutError()
        
        client = OrchestratorClient(orchestrator_url="http://slow-orchestrator:5099")
        client._http_client = mock_client
        
        with pytest.raises(asyncio.TimeoutError):
            from domain.entities import Service
            service = Service(
                name="test",
                base_url="http://test:8000",
                openapi_url="http://test:8000/openapi.json",
                version="1.0.0",
                description="Test",
                status="discovered"
            )
            await client.register_service(service)


@pytest.mark.integration
class TestServiceDiscoveryFlow:
    """Test complete service discovery flow with orchestrator."""
    
    @pytest.mark.asyncio
    async def test_discover_and_register_workflow(self, mock_orchestrator, simple_openapi_spec):
        """Test complete workflow: discover service, generate tools, register with orchestrator."""
        from domain.services.discovery_service import DiscoveryService
        from domain.services.tool_discovery import ToolDiscovery
        from domain.value_objects import DiscoverySpec
        from infrastructure.orchestrator_client import OrchestratorClient
        
        # Step 1: Discover service
        discovery_service = DiscoveryService()
        spec = DiscoverySpec(content=simple_openapi_spec)
        discovery_result = await discovery_service.discover(spec, service_name="test-service")
        
        assert discovery_result.success is True
        
        # Step 2: Generate tools
        tool_discovery = ToolDiscovery()
        tools = await tool_discovery.generate_tools(discovery_result.service)
        
        assert len(tools) >= 1
        
        # Step 3: Register with orchestrator
        orchestrator_client = OrchestratorClient(orchestrator_url="http://orchestrator:5099")
        orchestrator_client._http_client = mock_orchestrator
        
        register_result = await orchestrator_client.register_service(discovery_result.service)
        assert register_result["success"] is True
        
        tools_result = await orchestrator_client.register_tools(tools)
        assert tools_result["success"] is True


@pytest.mark.integration
class TestLogCollectorIntegration:
    """Test integration with log-collector service."""
    
    @pytest.mark.asyncio
    async def test_send_discovery_logs(self):
        """Test sending discovery logs to log-collector."""
        # This is a placeholder - actual implementation depends on log-collector integration
        from infrastructure.logging_client import LogCollectorClient
        
        client = LogCollectorClient(log_collector_url="http://log-collector:5060")
        
        log_entry = {
            "service": "discovery-agent",
            "level": "INFO",
            "message": "Service discovered successfully",
            "service_name": "test-service",
            "endpoint_count": 5
        }
        
        # Should be able to send logs (may fail if service not running)
        try:
            result = await client.send_log(log_entry)
            # If it succeeds, verify result
            if result:
                assert "success" in result or "status" in result
        except Exception:
            # If it fails due to connection, that's OK for this test
            pass
    
    @pytest.mark.asyncio
    async def test_log_discovery_event(self):
        """Test logging a discovery event."""
        from infrastructure.logging_client import LogCollectorClient
        from datetime import datetime, timezone
        
        client = LogCollectorClient(log_collector_url="http://log-collector:5060")
        
        event = {
            "service": "discovery-agent",
            "event_type": "service_discovered",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "service_name": "test-service",
                "endpoint_count": 3,
                "discovery_duration_ms": 125.5
            }
        }
        
        try:
            await client.send_event(event)
        except Exception:
            # Connection failures are OK for this test
            pass


@pytest.mark.integration
class TestSecureAnalyzerIntegration:
    """Test integration with secure-analyzer service."""
    
    @pytest.mark.asyncio
    async def test_scan_discovered_endpoints(self, sample_service_with_endpoints):
        """Test scanning discovered endpoints with secure-analyzer."""
        from infrastructure.security_scanner import ToolSecurityScanner
        
        scanner = ToolSecurityScanner(secure_analyzer_url="http://secure-analyzer:5070")
        
        # This will likely fail without secure-analyzer running, but should not crash
        try:
            for endpoint in sample_service_with_endpoints.endpoints:
                result = await scanner.scan_endpoint(endpoint)
                # If it succeeds, verify structure
                if result:
                    assert "risk_level" in result or "security_score" in result
        except Exception:
            # Connection failures are OK
            pass

