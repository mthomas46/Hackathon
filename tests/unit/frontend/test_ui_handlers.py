"""Comprehensive UI Handlers Tests.

Tests for all frontend UI handler modules including service-specific handlers,
main handlers, workflow handlers, and cross-service integrations.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
from fastapi.testclient import TestClient

# Adjust path for local imports
import sys
from pathlib import Path

# Add the Frontend service directory to Python path
frontend_path = Path(__file__).parent.parent.parent.parent / "services" / "frontend"
sys.path.insert(0, str(frontend_path))

from modules.ui_handlers.main_handlers import MainHandlers
from modules.ui_handlers.workflow_handlers import WorkflowHandlers
from modules.ui_handlers.services_overview_handlers import ServicesOverviewHandlers
from modules.ui_handlers.doc_store_handlers import DocStoreHandlers
from modules.ui_handlers.prompt_store_handlers import PromptStoreHandlers

# Test markers for parallel execution and categorization
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.frontend
]


@pytest.fixture
def mock_service_clients():
    """Mock service clients for testing."""
    with patch('modules.shared.clients.ServiceClients') as mock_clients_class:
        mock_clients = MagicMock()
        mock_clients_class.return_value = mock_clients

        # Mock various service responses
        mock_clients.get_json = AsyncMock(return_value={
            "success": True,
            "data": {"status": "healthy", "version": "1.0.0"}
        })
        mock_clients.post_json = AsyncMock(return_value={
            "success": True,
            "data": {"result": "processed"}
        })

        yield mock_clients


@pytest.fixture
def main_handlers(mock_service_clients):
    """Create MainHandlers instance for testing."""
    return MainHandlers()


@pytest.fixture
def workflow_handlers(mock_service_clients):
    """Create WorkflowHandlers instance for testing."""
    return WorkflowHandlers()


@pytest.fixture
def services_overview_handlers(mock_service_clients):
    """Create ServicesOverviewHandlers instance for testing."""
    return ServicesOverviewHandlers()


class TestMainHandlers:
    """Comprehensive tests for main UI handlers."""

    def test_get_main_dashboard(self, main_handlers):
        """Test main dashboard rendering."""
        # Mock template rendering
        with patch('modules.ui_handlers.main_handlers.render_template') as mock_render:
            mock_render.return_value = "<html>Main Dashboard</html>"

            result = main_handlers.get_main_dashboard()

            assert result is not None
            mock_render.assert_called_once()
            call_args = mock_render.call_args
            assert "main_dashboard" in call_args[0][0]

    def test_get_health_status(self, main_handlers):
        """Test health status endpoint."""
        result = main_handlers.get_health_status()

        assert isinstance(result, dict)
        assert "status" in result
        assert "timestamp" in result
        assert "version" in result

    def test_get_service_info(self, main_handlers):
        """Test service info endpoint."""
        result = main_handlers.get_service_info()

        assert isinstance(result, dict)
        assert "service" in result
        assert "version" in result
        assert "description" in result

    def test_get_environment_config(self, main_handlers):
        """Test environment configuration retrieval."""
        result = main_handlers.get_environment_config()

        assert isinstance(result, dict)
        assert "REPORTING_URL" in result
        assert "DOC_STORE_URL" in result
        assert "ORCHESTRATOR_URL" in result

    def test_render_error_page(self, main_handlers):
        """Test error page rendering."""
        with patch('modules.ui_handlers.main_handlers.render_template') as mock_render:
            mock_render.return_value = "<html>Error Page</html>"

            result = main_handlers.render_error_page("Test Error", 500)

            assert result is not None
            mock_render.assert_called_once()

    def test_validate_service_connectivity(self, main_handlers, mock_service_clients):
        """Test service connectivity validation."""
        result = main_handlers.validate_service_connectivity()

        assert isinstance(result, dict)
        assert "overall_status" in result
        assert "services" in result
        assert "last_checked" in result

    def test_get_navigation_menu(self, main_handlers):
        """Test navigation menu generation."""
        result = main_handlers.get_navigation_menu()

        assert isinstance(result, dict)
        assert "menu_items" in result
        assert "active_section" in result

        menu_items = result["menu_items"]
        assert isinstance(menu_items, list)
        assert len(menu_items) > 0

        # Check for essential menu items
        menu_names = [item.get("name") for item in menu_items]
        assert "Dashboard" in menu_names
        assert "Services" in menu_names
        assert "Workflows" in menu_names

    def test_get_system_metrics(self, main_handlers):
        """Test system metrics retrieval."""
        result = main_handlers.get_system_metrics()

        assert isinstance(result, dict)
        assert "memory_usage" in result
        assert "cpu_usage" in result
        assert "active_connections" in result
        assert "uptime" in result


class TestWorkflowHandlers:
    """Comprehensive tests for workflow UI handlers."""

    def test_get_workflow_status_dashboard(self, workflow_handlers):
        """Test workflow status dashboard."""
        with patch('modules.ui_handlers.workflow_handlers.render_template') as mock_render:
            mock_render.return_value = "<html>Workflow Dashboard</html>"

            result = workflow_handlers.get_workflow_status_dashboard()

            assert result is not None
            mock_render.assert_called_once()

    def test_get_active_workflows(self, workflow_handlers, mock_service_clients):
        """Test active workflows retrieval."""
        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "workflows": [
                    {"id": "wf-1", "status": "running", "type": "document_analysis"},
                    {"id": "wf-2", "status": "completed", "type": "code_review"}
                ]
            }
        }

        result = workflow_handlers.get_active_workflows()

        assert isinstance(result, dict)
        assert "workflows" in result
        assert len(result["workflows"]) == 2

    def test_get_workflow_details(self, workflow_handlers, mock_service_clients):
        """Test individual workflow details retrieval."""
        workflow_id = "test-workflow-123"

        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "id": workflow_id,
                "status": "running",
                "steps": [
                    {"name": "fetch_documents", "status": "completed"},
                    {"name": "analyze_content", "status": "running"}
                ]
            }
        }

        result = workflow_handlers.get_workflow_details(workflow_id)

        assert isinstance(result, dict)
        assert result["id"] == workflow_id
        assert result["status"] == "running"
        assert len(result["steps"]) == 2

    def test_create_workflow_from_template(self, workflow_handlers, mock_service_clients):
        """Test workflow creation from template."""
        template_data = {
            "template": "document_analysis",
            "parameters": {
                "doc_ids": ["doc-1", "doc-2"],
                "analysis_type": "comprehensive"
            }
        }

        mock_service_clients.post_json.return_value = {
            "success": True,
            "data": {
                "workflow_id": "wf-new-123",
                "status": "created"
            }
        }

        result = workflow_handlers.create_workflow_from_template(template_data)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"]["workflow_id"] == "wf-new-123"

    def test_cancel_workflow(self, workflow_handlers, mock_service_clients):
        """Test workflow cancellation."""
        workflow_id = "wf-cancel-123"

        mock_service_clients.post_json.return_value = {
            "success": True,
            "data": {"status": "cancelled"}
        }

        result = workflow_handlers.cancel_workflow(workflow_id)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"]["status"] == "cancelled"

    def test_get_workflow_templates(self, workflow_handlers):
        """Test workflow templates retrieval."""
        result = workflow_handlers.get_workflow_templates()

        assert isinstance(result, dict)
        assert "templates" in result

        templates = result["templates"]
        assert isinstance(templates, list)
        assert len(templates) > 0

        # Check for essential templates
        template_names = [t.get("name") for t in templates]
        assert "document_analysis" in template_names

    def test_get_workflow_history(self, workflow_handlers, mock_service_clients):
        """Test workflow execution history."""
        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "history": [
                    {"id": "wf-1", "status": "completed", "duration": 45},
                    {"id": "wf-2", "status": "failed", "duration": 12}
                ]
            }
        }

        result = workflow_handlers.get_workflow_history()

        assert isinstance(result, dict)
        assert "history" in result
        assert len(result["history"]) == 2

    def test_validate_workflow_parameters(self, workflow_handlers):
        """Test workflow parameter validation."""
        valid_params = {
            "doc_ids": ["doc-1", "doc-2"],
            "analysis_type": "comprehensive"
        }

        result = workflow_handlers.validate_workflow_parameters("document_analysis", valid_params)
        assert result["valid"] is True

        invalid_params = {
            "invalid_field": "value"
        }

        result = workflow_handlers.validate_workflow_parameters("document_analysis", invalid_params)
        assert result["valid"] is False
        assert "errors" in result


class TestServicesOverviewHandlers:
    """Comprehensive tests for services overview handlers."""

    def test_get_services_overview_dashboard(self, services_overview_handlers):
        """Test services overview dashboard."""
        with patch('modules.ui_handlers.services_overview_handlers.render_template') as mock_render:
            mock_render.return_value = "<html>Services Overview</html>"

            result = services_overview_handlers.get_services_overview_dashboard()

            assert result is not None
            mock_render.assert_called_once()

    def test_get_service_health_status(self, services_overview_handlers, mock_service_clients):
        """Test service health status retrieval."""
        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": "2h 30m",
                "last_check": "2024-01-15T10:30:00Z"
            }
        }

        result = services_overview_handlers.get_service_health_status("orchestrator")

        assert isinstance(result, dict)
        assert result["status"] == "healthy"
        assert result["version"] == "1.0.0"

    def test_get_all_services_status(self, services_overview_handlers, mock_service_clients):
        """Test all services status retrieval."""
        mock_service_clients.get_json.side_effect = [
            {"success": True, "data": {"status": "healthy"}},  # orchestrator
            {"success": True, "data": {"status": "healthy"}},  # doc_store
            {"success": False, "data": {"status": "unhealthy", "error": "timeout"}}  # analysis_service
        ]

        result = services_overview_handlers.get_all_services_status()

        assert isinstance(result, dict)
        assert "services" in result
        assert "overall_health" in result

        services = result["services"]
        assert len(services) >= 3  # At least 3 services checked

    def test_get_service_metrics(self, services_overview_handlers, mock_service_clients):
        """Test service metrics retrieval."""
        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "requests_per_minute": 45,
                "average_response_time": 120,
                "error_rate": 0.02,
                "active_connections": 12
            }
        }

        result = services_overview_handlers.get_service_metrics("doc_store")

        assert isinstance(result, dict)
        assert "requests_per_minute" in result
        assert "average_response_time" in result
        assert "error_rate" in result

    def test_get_service_dependencies(self, services_overview_handlers):
        """Test service dependency mapping."""
        result = services_overview_handlers.get_service_dependencies("orchestrator")

        assert isinstance(result, dict)
        assert "service" in result
        assert "dependencies" in result
        assert "dependents" in result

        dependencies = result["dependencies"]
        assert isinstance(dependencies, list)

    def test_refresh_service_status(self, services_overview_handlers, mock_service_clients):
        """Test service status refresh."""
        mock_service_clients.post_json.return_value = {
            "success": True,
            "data": {"refreshed": True, "timestamp": "2024-01-15T10:35:00Z"}
        }

        result = services_overview_handlers.refresh_service_status("doc_store")

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"]["refreshed"] is True

    def test_get_service_logs(self, services_overview_handlers, mock_service_clients):
        """Test service logs retrieval."""
        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "logs": [
                    {"timestamp": "2024-01-15T10:30:00Z", "level": "INFO", "message": "Service started"},
                    {"timestamp": "2024-01-15T10:35:00Z", "level": "WARN", "message": "High memory usage"}
                ]
            }
        }

        result = services_overview_handlers.get_service_logs("orchestrator", limit=10)

        assert isinstance(result, dict)
        assert "logs" in result
        assert len(result["logs"]) == 2

    def test_service_connectivity_test(self, services_overview_handlers, mock_service_clients):
        """Test service connectivity testing."""
        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {"connectivity": "ok", "latency": 45}
        }

        result = services_overview_handlers.test_service_connectivity("doc_store")

        assert isinstance(result, dict)
        assert result["connectivity"] == "ok"
        assert "latency" in result


class TestDocStoreHandlers:
    """Comprehensive tests for document store UI handlers."""

    @pytest.fixture
    def doc_store_handlers(self, mock_service_clients):
        """Create DocStoreHandlers instance for testing."""
        return DocStoreHandlers()

    def test_get_document_browser(self, doc_store_handlers):
        """Test document browser interface."""
        with patch('modules.ui_handlers.doc_store_handlers.render_template') as mock_render:
            mock_render.return_value = "<html>Document Browser</html>"

            result = doc_store_handlers.get_document_browser()

            assert result is not None
            mock_render.assert_called_once()

    def test_search_documents(self, doc_store_handlers, mock_service_clients):
        """Test document search functionality."""
        mock_service_clients.post_json.return_value = {
            "success": True,
            "data": {
                "results": [
                    {"id": "doc-1", "title": "API Documentation", "score": 0.95},
                    {"id": "doc-2", "title": "User Guide", "score": 0.87}
                ],
                "total": 2,
                "page": 1
            }
        }

        query = "API documentation"
        result = doc_store_handlers.search_documents(query)

        assert isinstance(result, dict)
        assert "results" in result
        assert len(result["results"]) == 2
        assert result["total"] == 2

    def test_get_document_details(self, doc_store_handlers, mock_service_clients):
        """Test individual document details retrieval."""
        doc_id = "test-doc-123"

        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "document": {
                    "id": doc_id,
                    "title": "Test Document",
                    "content": "Test content",
                    "metadata": {"author": "test-user", "created": "2024-01-15"}
                }
            }
        }

        result = doc_store_handlers.get_document_details(doc_id)

        assert isinstance(result, dict)
        assert result["document"]["id"] == doc_id
        assert result["document"]["title"] == "Test Document"

    def test_create_document(self, doc_store_handlers, mock_service_clients):
        """Test document creation."""
        doc_data = {
            "title": "New Test Document",
            "content": "This is test content",
            "metadata": {"author": "test-user", "tags": ["test"]}
        }

        mock_service_clients.post_json.return_value = {
            "success": True,
            "data": {
                "document_id": "new-doc-123",
                "status": "created"
            }
        }

        result = doc_store_handlers.create_document(doc_data)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"]["document_id"] == "new-doc-123"

    def test_update_document(self, doc_store_handlers, mock_service_clients):
        """Test document updates."""
        doc_id = "update-doc-123"
        update_data = {
            "title": "Updated Title",
            "content": "Updated content"
        }

        mock_service_clients.put_json.return_value = {
            "success": True,
            "data": {"updated": True, "timestamp": "2024-01-15T11:00:00Z"}
        }

        result = doc_store_handlers.update_document(doc_id, update_data)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"]["updated"] is True

    def test_delete_document(self, doc_store_handlers, mock_service_clients):
        """Test document deletion."""
        doc_id = "delete-doc-123"

        mock_service_clients.delete_json.return_value = {
            "success": True,
            "data": {"deleted": True}
        }

        result = doc_store_handlers.delete_document(doc_id)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"]["deleted"] is True

    def test_get_document_versions(self, doc_store_handlers, mock_service_clients):
        """Test document version history."""
        doc_id = "version-doc-123"

        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "versions": [
                    {"version": 1, "timestamp": "2024-01-10", "author": "user1"},
                    {"version": 2, "timestamp": "2024-01-12", "author": "user2"},
                    {"version": 3, "timestamp": "2024-01-15", "author": "user1"}
                ]
            }
        }

        result = doc_store_handlers.get_document_versions(doc_id)

        assert isinstance(result, dict)
        assert "versions" in result
        assert len(result["versions"]) == 3

    def test_bulk_document_operations(self, doc_store_handlers, mock_service_clients):
        """Test bulk document operations."""
        doc_ids = ["doc-1", "doc-2", "doc-3"]
        operation = "tag"
        tag_data = {"tags": ["bulk-test"]}

        mock_service_clients.post_json.return_value = {
            "success": True,
            "data": {
                "processed": 3,
                "successful": 3,
                "failed": 0
            }
        }

        result = doc_store_handlers.bulk_document_operations(doc_ids, operation, tag_data)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"]["processed"] == 3
        assert result["data"]["successful"] == 3


class TestPromptStoreHandlers:
    """Comprehensive tests for prompt store UI handlers."""

    @pytest.fixture
    def prompt_store_handlers(self, mock_service_clients):
        """Create PromptStoreHandlers instance for testing."""
        return PromptStoreHandlers()

    def test_get_prompt_browser(self, prompt_store_handlers):
        """Test prompt browser interface."""
        with patch('modules.ui_handlers.prompt_store_handlers.render_template') as mock_render:
            mock_render.return_value = "<html>Prompt Browser</html>"

            result = prompt_store_handlers.get_prompt_browser()

            assert result is not None
            mock_render.assert_called_once()

    def test_get_prompt_details(self, prompt_store_handlers, mock_service_clients):
        """Test individual prompt details retrieval."""
        prompt_id = "test-prompt-123"

        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "prompt": {
                    "id": prompt_id,
                    "name": "Document Analysis Prompt",
                    "content": "Analyze the following document for...",
                    "category": "analysis",
                    "variables": ["document_content", "analysis_type"]
                }
            }
        }

        result = prompt_store_handlers.get_prompt_details(prompt_id)

        assert isinstance(result, dict)
        assert result["prompt"]["id"] == prompt_id
        assert result["prompt"]["name"] == "Document Analysis Prompt"

    def test_create_prompt(self, prompt_store_handlers, mock_service_clients):
        """Test prompt creation."""
        prompt_data = {
            "name": "New Analysis Prompt",
            "content": "Perform comprehensive analysis...",
            "category": "analysis",
            "variables": ["content", "context"]
        }

        mock_service_clients.post_json.return_value = {
            "success": True,
            "data": {
                "prompt_id": "new-prompt-123",
                "status": "created"
            }
        }

        result = prompt_store_handlers.create_prompt(prompt_data)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"]["prompt_id"] == "new-prompt-123"

    def test_update_prompt(self, prompt_store_handlers, mock_service_clients):
        """Test prompt updates."""
        prompt_id = "update-prompt-123"
        update_data = {
            "content": "Updated analysis prompt content...",
            "variables": ["content", "analysis_depth"]
        }

        mock_service_clients.put_json.return_value = {
            "success": True,
            "data": {"updated": True, "version": 2}
        }

        result = prompt_store_handlers.update_prompt(prompt_id, update_data)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"]["updated"] is True

    def test_fork_prompt(self, prompt_store_handlers, mock_service_clients):
        """Test prompt forking."""
        prompt_id = "fork-prompt-123"
        fork_data = {
            "name": "Forked Analysis Prompt",
            "modifications": "Added additional context requirements"
        }

        mock_service_clients.post_json.return_value = {
            "success": True,
            "data": {
                "original_id": prompt_id,
                "forked_id": "forked-prompt-456",
                "differences": ["name", "modifications"]
            }
        }

        result = prompt_store_handlers.fork_prompt(prompt_id, fork_data)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"]["forked_id"] == "forked-prompt-456"

    def test_search_prompts(self, prompt_store_handlers, mock_service_clients):
        """Test prompt search functionality."""
        mock_service_clients.post_json.return_value = {
            "success": True,
            "data": {
                "results": [
                    {"id": "prompt-1", "name": "Analysis Prompt", "score": 0.92},
                    {"id": "prompt-2", "name": "Summary Prompt", "score": 0.85}
                ],
                "total": 2
            }
        }

        query = "analysis prompt"
        result = prompt_store_handlers.search_prompts(query)

        assert isinstance(result, dict)
        assert "results" in result
        assert len(result["results"]) == 2

    def test_get_prompt_categories(self, prompt_store_handlers, mock_service_clients):
        """Test prompt categories retrieval."""
        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "categories": [
                    {"name": "analysis", "count": 15, "description": "Document analysis prompts"},
                    {"name": "summary", "count": 8, "description": "Summarization prompts"},
                    {"name": "generation", "count": 12, "description": "Content generation prompts"}
                ]
            }
        }

        result = prompt_store_handlers.get_prompt_categories()

        assert isinstance(result, dict)
        assert "categories" in result
        assert len(result["categories"]) == 3

    def test_validate_prompt_syntax(self, prompt_store_handlers):
        """Test prompt syntax validation."""
        valid_prompt = {
            "content": "Analyze {{document}} for {{criteria}}",
            "variables": ["document", "criteria"]
        }

        result = prompt_store_handlers.validate_prompt_syntax(valid_prompt)
        assert result["valid"] is True

        invalid_prompt = {
            "content": "Analyze {{document}} for undefined variable",
            "variables": ["document"]  # Missing 'undefined'
        }

        result = prompt_store_handlers.validate_prompt_syntax(invalid_prompt)
        assert result["valid"] is False
        assert "errors" in result

    def test_get_prompt_usage_stats(self, prompt_store_handlers, mock_service_clients):
        """Test prompt usage statistics."""
        prompt_id = "stats-prompt-123"

        mock_service_clients.get_json.return_value = {
            "success": True,
            "data": {
                "usage": {
                    "total_calls": 150,
                    "successful_calls": 145,
                    "average_response_time": 2.3,
                    "last_used": "2024-01-15T10:30:00Z"
                }
            }
        }

        result = prompt_store_handlers.get_prompt_usage_stats(prompt_id)

        assert isinstance(result, dict)
        assert "usage" in result
        assert result["usage"]["total_calls"] == 150
        assert result["usage"]["successful_calls"] == 145
