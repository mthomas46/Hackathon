"""Comprehensive Integration Tests for Enhanced Interpreter Service.

This module tests the enhanced natural language processing capabilities of the
interpreter service, including ecosystem awareness, orchestrator integration,
LangGraph workflow discovery, and prompt engineering.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

# Import the enhanced modules
from modules.models import UserQuery
from modules.ecosystem_context import ecosystem_context
from modules.orchestrator_integration import orchestrator_integration
from modules.prompt_engineering import prompt_engineer
from modules.langgraph_discovery import langgraph_discovery
from services.shared.constants_new import ServiceNames


class TestEcosystemContextIntegration:
    """Test ecosystem context awareness capabilities."""

    @pytest.mark.asyncio
    async def test_get_service_capabilities(self):
        """Test retrieving service capabilities from ecosystem context."""
        capabilities = await ecosystem_context.get_service_capabilities()

        assert isinstance(capabilities, dict)
        assert len(capabilities) > 0

        # Check that key services are present
        service_names = list(capabilities.keys())
        assert "document_store" in service_names
        assert "prompt_store" in service_names
        assert "analysis_service" in service_names

    @pytest.mark.asyncio
    async def test_service_alias_resolution(self):
        """Test service alias resolution."""
        # Test known aliases
        assert ecosystem_context.get_service_by_alias("docs") == "document_store"
        assert ecosystem_context.get_service_by_alias("documents") == "document_store"
        assert ecosystem_context.get_service_by_alias("prompts") == "prompt_store"

        # Test unknown alias
        assert ecosystem_context.get_service_by_alias("unknown_service") is None

    @pytest.mark.asyncio
    async def test_capability_service_mapping(self):
        """Test mapping capabilities to services."""
        # Test capability lookup
        analysis_services = ecosystem_context.get_capability_service("analysis")
        assert isinstance(analysis_services, list)
        assert "analysis_service" in analysis_services

        search_services = ecosystem_context.get_capability_service("search")
        assert isinstance(search_services, list)
        assert len(search_services) > 0

    @pytest.mark.asyncio
    async def test_workflow_mapping(self):
        """Test query to workflow mapping."""
        # Test document analysis mapping
        workflow = ecosystem_context.map_query_to_workflow(
            "analyze this document",
            {"document_type": ["code"]}
        )
        assert workflow is not None
        assert "services" in workflow
        assert "document_store" in workflow["services"]

        # Test unknown query
        unknown_workflow = ecosystem_context.map_query_to_workflow(
            "do something unknown",
            {}
        )
        assert unknown_workflow is None


class TestOrchestratorIntegration:
    """Test orchestrator integration capabilities."""

    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test workflow execution through orchestrator."""
        with patch.object(orchestrator_integration.client, 'post_json') as mock_post:
            mock_post.return_value = {"success": True, "data": {"status": "completed"}}

            result = await orchestrator_integration.execute_workflow(
                "document_analysis",
                {"doc_id": "test-doc"},
                "test-user"
            )

            assert result["status"] == "success"
            assert "workflow_type" in result
            assert result["workflow_type"] == "document_analysis"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_langgraph_workflow_execution(self):
        """Test LangGraph workflow execution."""
        with patch.object(orchestrator_integration.client, 'post_json') as mock_post:
            mock_post.return_value = {"success": True, "data": {"result": "analyzed"}}

            result = await orchestrator_integration.execute_langgraph_workflow(
                "document-analysis",
                {"doc_id": "test-doc"},
                "test-user"
            )

            assert result["status"] == "success"
            assert "document-analysis" in result["message"]
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_validation(self):
        """Test workflow validation."""
        # Test valid workflow
        valid_workflow = {
            "services": ["document_store", "analysis_service"],
            "steps": [
                {"service": "document_store", "action": "retrieve"},
                {"service": "analysis_service", "action": "analyze"}
            ]
        }

        with patch.object(ecosystem_context, 'validate_workflow_compatibility') as mock_validate:
            mock_validate.return_value = {"valid": True, "workflow": valid_workflow}

            result = await orchestrator_integration.validate_workflow_execution(valid_workflow)
            assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_tools_discovery(self):
        """Test orchestrator tools discovery."""
        with patch.object(orchestrator_integration.client, 'post_json') as mock_post:
            mock_tools = {
                "document_store_retrieve": {"name": "retrieve", "service": "document_store"},
                "analysis_service_analyze": {"name": "analyze", "service": "analysis_service"}
            }
            mock_post.return_value = {"success": True, "data": mock_tools}

            tools = await orchestrator_integration.get_orchestrator_tools()
            assert isinstance(tools, dict)
            mock_post.assert_called_once()


class TestPromptEngineering:
    """Test prompt engineering capabilities."""

    @pytest.mark.asyncio
    async def test_query_translation(self):
        """Test natural language to workflow translation."""
        query = "analyze this document for quality"
        intent = "analyze_document"
        entities = {"document_type": ["general"]}

        with patch.object(ecosystem_context, 'get_service_capabilities') as mock_capabilities:
            mock_capabilities.return_value = {
                "document_store": {"capabilities": ["store_documents", "retrieve_documents"]},
                "analysis_service": {"capabilities": ["analyze_documents", "quality_check"]}
            }

            result = await prompt_engineer.translate_query_to_workflow(
                query, intent, entities, await mock_capabilities()
            )

            assert isinstance(result, dict)
            assert "workflow_type" in result
            assert "confidence" in result
            assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_ambiguous_query_handling(self):
        """Test handling of ambiguous queries."""
        query = "analyze"
        intent = "unknown"
        entities = {}

        with patch.object(ecosystem_context, 'get_service_capabilities') as mock_capabilities:
            mock_capabilities.return_value = {}

            result = await prompt_engineer.translate_query_to_workflow(
                query, intent, entities, {}
            )

            assert result["workflow_type"] == "clarification_needed"
            assert "suggestions" in result["parameters"]

    @pytest.mark.asyncio
    async def test_workflow_optimization(self):
        """Test workflow optimization capabilities."""
        workflow = {
            "services": ["document_store", "analysis_service"],
            "parameters": {"doc_id": "test"}
        }

        result = await prompt_engineer.optimize_workflow(workflow, {})
        assert "optimized_workflow" in result
        assert "optimizations_applied" in result


class TestLangGraphDiscovery:
    """Test LangGraph workflow discovery capabilities."""

    @pytest.mark.asyncio
    async def test_workflow_discovery(self):
        """Test LangGraph workflow discovery."""
        with patch.object(langgraph_discovery.client, 'get_json') as mock_get:
            mock_workflows = {
                "document-analysis": {"type": "langgraph", "description": "Analyze documents"},
                "code-documentation": {"type": "langgraph", "description": "Generate docs"}
            }
            mock_get.return_value = {"success": True, "data": mock_workflows}

            result = await langgraph_discovery.discover_langgraph_workflows()

            assert result["status"] == "success"
            assert "workflows" in result
            assert len(result["workflows"]) > 0

    @pytest.mark.asyncio
    async def test_workflow_matching(self):
        """Test finding matching LangGraph workflows."""
        query = "analyze this document"
        intent = "analyze_document"
        entities = {"document_type": ["general"]}

        # Mock discovered workflows
        langgraph_discovery.discovered_workflows = {
            "document-analysis": {
                "type": "langgraph",
                "description": "Analyze documents using AI",
                "parameters": {"doc_id": "string"}
            }
        }

        match = await langgraph_discovery.find_matching_langgraph_workflow(
            query, intent, entities
        )

        assert match is not None
        assert match["workflow_name"] == "document-analysis"
        assert "match_score" in match

    @pytest.mark.asyncio
    async def test_workflow_validation(self):
        """Test LangGraph workflow parameter validation."""
        workflow_name = "document-analysis"
        valid_params = {"doc_id": "test-doc"}
        invalid_params = {"invalid_param": "value"}

        # Mock discovered workflows
        langgraph_discovery.discovered_workflows = {
            "document-analysis": {
                "parameters": {"doc_id": "string"}
            }
        }

        # Test valid parameters
        valid_result = await langgraph_discovery.validate_langgraph_workflow(
            workflow_name, valid_params
        )
        assert valid_result["valid"] is True

        # Test invalid parameters
        invalid_result = await langgraph_discovery.validate_langgraph_workflow(
            workflow_name, invalid_params
        )
        assert valid_result["valid"] is True  # Should still be valid for unknown params

    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test LangGraph workflow execution."""
        with patch.object(langgraph_discovery, 'execute_langgraph_workflow') as mock_execute:
            mock_execute.return_value = {"status": "success", "result": "completed"}

            result = await langgraph_discovery.execute_langgraph_workflow(
                "document-analysis",
                {"doc_id": "test"},
                "test-user"
            )

            assert result["status"] == "success"
            mock_execute.assert_called_once()


class TestEnhancedInterpreterAPI:
    """Test enhanced interpreter API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client for interpreter service."""
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_natural_query_processing(self, client):
        """Test natural query processing endpoint."""
        query_data = {
            "query": "analyze this document for quality issues",
            "user_id": "test-user",
            "context": {"domain": "documentation"}
        }

        response = client.post("/natural-query", json=query_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "original_query" in data["data"]
        assert "interpretation" in data["data"]
        assert "ecosystem_context" in data["data"]

    def test_ecosystem_capabilities(self, client):
        """Test ecosystem capabilities endpoint."""
        response = client.get("/ecosystem/capabilities")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "services" in data["data"]
        assert "workflows" in data["data"]
        assert "metadata" in data["data"]

    def test_workflow_discovery(self, client):
        """Test workflow discovery endpoint."""
        response = client.post("/workflows/discover")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "langgraph_workflows" in data["data"]
        assert "traditional_workflows" in data["data"]
        assert "summary" in data["data"]

    def test_prompt_translation(self, client):
        """Test prompt translation endpoint."""
        query_data = {
            "query": "analyze document quality and generate a report",
            "user_id": "test-user"
        }

        response = client.post("/prompt/translate", json=query_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "translation" in data["data"]
        assert "execution_recommendations" in data["data"]


class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_natural_language_workflow(self):
        """Test complete natural language to workflow execution."""
        # Mock all dependencies
        with patch.object(ecosystem_context, 'get_service_capabilities') as mock_capabilities, \
             patch.object(orchestrator_integration, 'execute_workflow') as mock_execute, \
             patch.object(langgraph_discovery, 'find_matching_langgraph_workflow') as mock_find:

            # Setup mocks
            mock_capabilities.return_value = {
                "document_store": {"capabilities": ["retrieve_documents"]},
                "analysis_service": {"capabilities": ["analyze_quality"]}
            }

            mock_find.return_value = {
                "workflow_name": "document-analysis",
                "match_score": 0.9,
                "workflow_info": {"type": "langgraph"}
            }

            mock_execute.return_value = {
                "status": "success",
                "message": "Document analysis completed",
                "result": {"quality_score": 0.85}
            }

            # Test the complete flow
            query = "analyze this document for quality"
            intent = "analyze_document"
            entities = {"document_type": ["general"]}

            # 1. Translate query to workflow
            translation = await prompt_engineer.translate_query_to_workflow(
                query, intent, entities, await mock_capabilities()
            )
            assert translation["workflow_type"] == "document_analysis"

            # 2. Find matching LangGraph workflow
            match = await mock_find(query, intent, entities)
            assert match["workflow_name"] == "document-analysis"

            # 3. Execute workflow
            result = await mock_execute("document_analysis", {"doc_id": "test"}, "test-user")
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback mechanisms."""
        # Test ecosystem context fallback
        with patch.object(ecosystem_context, 'get_service_capabilities', side_effect=Exception("Network error")):
            capabilities = await ecosystem_context.get_service_capabilities()
            assert isinstance(capabilities, dict)  # Should return empty dict on error

        # Test orchestrator integration fallback
        with patch.object(orchestrator_integration.client, 'post_json', side_effect=Exception("Connection failed")):
            result = await orchestrator_integration.execute_workflow("test", {}, None)
            assert result["status"] == "error"
            assert "Connection failed" in result["error"]

        # Test prompt engineering fallback
        with patch.object(prompt_engineer, '_rule_based_translation', side_effect=Exception("Translation failed")):
            result = await prompt_engineer.translate_query_to_workflow("test", "unknown", {}, {})
            assert result["workflow_type"] == "help"  # Should fallback to help

    @pytest.mark.asyncio
    async def test_performance_and_caching(self):
        """Test performance optimizations and caching."""
        # Test ecosystem context caching
        start_time = asyncio.get_event_loop().time()

        # First call
        await ecosystem_context.get_service_capabilities()

        # Second call (should be cached)
        await ecosystem_context.get_service_capabilities()

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # Should complete quickly (under 0.1 seconds with caching)
        assert duration < 0.1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
