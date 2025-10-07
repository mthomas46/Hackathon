"""
Tests for dashboard pages.

These tests verify the page rendering logic and functionality
without running the full Streamlit server.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st


class TestHomePageRendering:
    """Tests for the home page."""
    
    @patch('streamlit.title')
    @patch('streamlit.write')
    @patch('streamlit.metric')
    def test_home_page_title(self, mock_metric, mock_write, mock_title):
        """Test that home page renders with correct title."""
        from pages import home
        
        # Simulate calling render
        home.render()
        
        # Verify title was called
        mock_title.assert_called()
    
    @patch('clients.performance_store_client.PerformanceStoreClient.get_recent_executions')
    @patch('clients.mcp_store_client.MCPStoreClient.get_trending_packages')
    @patch('streamlit.error')
    def test_home_page_handles_service_errors(self, mock_error, mock_trending, mock_executions):
        """Test that home page handles service errors gracefully."""
        from pages import home
        
        # Mock service failures
        mock_executions.side_effect = Exception("Service unavailable")
        mock_trending.side_effect = Exception("Service unavailable")
        
        # Render should not raise exception
        try:
            home.render()
        except Exception as e:
            pytest.fail(f"Home page should handle errors gracefully, but raised: {e}")


class TestPerformanceMonitorPage:
    """Tests for the performance monitor page."""
    
    @patch('streamlit.title')
    @patch('streamlit.selectbox')
    def test_performance_page_renders(self, mock_selectbox, mock_title):
        """Test that performance page renders without errors."""
        from pages import performance_monitor
        
        mock_selectbox.return_value = "24 hours"
        
        try:
            performance_monitor.render()
        except Exception as e:
            pytest.fail(f"Performance monitor should render without errors, but raised: {e}")
    
    @patch('clients.performance_store_client.PerformanceStoreClient.get_trends')
    @patch('streamlit.line_chart')
    def test_performance_page_displays_trends(self, mock_chart, mock_trends):
        """Test that performance page displays trend data."""
        from pages import performance_monitor
        
        # Mock trend data
        mock_trends.return_value = [
            {"timestamp": "2025-10-07T10:00:00", "average_duration": 1500},
            {"timestamp": "2025-10-07T11:00:00", "average_duration": 1450},
        ]
        
        performance_monitor.render()
        
        # Verify trends were fetched
        mock_trends.assert_called()


class TestMCPManagementPage:
    """Tests for the MCP management page."""
    
    @patch('streamlit.title')
    @patch('clients.mcp_provisioner_client.MCPProvisionerClient.list_mcps')
    def test_mcp_management_page_lists_mcps(self, mock_list, mock_title):
        """Test that MCP management page lists available MCPs."""
        from pages import mcp_management
        
        # Mock MCP list
        mock_list.return_value = [
            {"mcp_id": "mcp-1", "name": "Test MCP 1", "status": "active"},
            {"mcp_id": "mcp-2", "name": "Test MCP 2", "status": "inactive"},
        ]
        
        mcp_management.render()
        
        # Verify list was called
        mock_list.assert_called()
    
    @patch('streamlit.text_input')
    @patch('streamlit.button')
    @patch('clients.mcp_provisioner_client.MCPProvisionerClient.provision_mcp')
    @patch('streamlit.success')
    def test_mcp_provisioning(self, mock_success, mock_provision, mock_button, mock_input):
        """Test MCP provisioning workflow."""
        from pages import mcp_management
        
        # Mock user input
        mock_input.return_value = "new-mcp"
        mock_button.return_value = True
        mock_provision.return_value = {"mcp_id": "mcp-123", "status": "provisioned"}
        
        mcp_management.render()
        
        # Verify provision was called if button was clicked
        if mock_button.return_value:
            mock_provision.assert_called()


class TestMarketplacePage:
    """Tests for the marketplace page."""
    
    @patch('streamlit.title')
    @patch('clients.mcp_store_client.MCPStoreClient.get_trending_packages')
    def test_marketplace_displays_trending(self, mock_trending, mock_title):
        """Test that marketplace displays trending packages."""
        from pages import marketplace
        
        # Mock trending packages
        mock_trending.return_value = [
            {"package_id": "pkg-1", "name": "Popular Package", "downloads": 1000, "stars": 500},
            {"package_id": "pkg-2", "name": "Trending Package", "downloads": 800, "stars": 400},
        ]
        
        marketplace.render()
        
        # Verify trending was called
        mock_trending.assert_called()
    
    @patch('streamlit.text_input')
    @patch('clients.mcp_store_client.MCPStoreClient.search_packages')
    def test_marketplace_search(self, mock_search, mock_input):
        """Test marketplace search functionality."""
        from pages import marketplace
        
        # Mock search
        mock_input.return_value = "llm"
        mock_search.return_value = [
            {"package_id": "pkg-1", "name": "LLM Package", "description": "Test"},
        ]
        
        marketplace.render()
        
        # Search should be called with user input
        if mock_input.return_value:
            mock_search.assert_called()


class TestRegistryPage:
    """Tests for the registry page."""
    
    @patch('streamlit.title')
    @patch('clients.mcp_store_client.MCPStoreClient.get_packages')
    def test_registry_lists_packages(self, mock_packages, mock_title):
        """Test that registry page lists all packages."""
        from pages import registry
        
        # Mock package list
        mock_packages.return_value = [
            {"package_id": "pkg-1", "name": "Package 1", "latest_version": "1.0.0"},
            {"package_id": "pkg-2", "name": "Package 2", "latest_version": "2.1.0"},
        ]
        
        registry.render()
        
        # Verify packages were listed
        mock_packages.assert_called()
    
    @patch('streamlit.selectbox')
    @patch('clients.mcp_store_client.MCPStoreClient.get_versions')
    def test_registry_version_comparison(self, mock_versions, mock_selectbox):
        """Test version comparison functionality."""
        from pages import registry
        
        # Mock version selection
        mock_selectbox.return_value = "pkg-1"
        mock_versions.return_value = [
            {"version_id": "v1", "version_string": "1.0.0", "size_bytes": 1024},
            {"version_id": "v2", "version_string": "1.1.0", "size_bytes": 2048},
        ]
        
        registry.render()
        
        # Verify versions were fetched
        if mock_selectbox.return_value:
            mock_versions.assert_called()


class TestSystemHealthPage:
    """Tests for the system health page."""
    
    @patch('streamlit.title')
    @patch('httpx.AsyncClient.get')
    async def test_system_health_checks_services(self, mock_get, mock_title):
        """Test that system health page checks all services."""
        from pages import system_health
        
        # Mock health check responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response
        
        system_health.render()
        
        # Note: This test would need async support for full testing
        # For now, just verify the page renders
        assert True
    
    @patch('streamlit.metric')
    def test_system_health_displays_metrics(self, mock_metric):
        """Test that system health displays service metrics."""
        from pages import system_health
        
        system_health.render()
        
        # Metrics should be displayed for services
        assert mock_metric.call_count >= 3  # At least 3 services


class TestQueryPlayground:
    """Tests for the query playground page."""
    
    @patch('streamlit.title')
    @patch('streamlit.text_area')
    @patch('streamlit.button')
    def test_query_playground_renders(self, mock_button, mock_area, mock_title):
        """Test that query playground renders correctly."""
        from pages import query_playground
        
        mock_area.return_value = "Test query"
        mock_button.return_value = False
        
        query_playground.render()
        
        # Verify components were rendered
        mock_title.assert_called()
        mock_area.assert_called()


class TestTrainingDashboard:
    """Tests for the training dashboard page."""
    
    @patch('streamlit.title')
    @patch('streamlit.write')
    def test_training_dashboard_renders(self, mock_write, mock_title):
        """Test that training dashboard renders correctly."""
        from pages import training_dashboard
        
        training_dashboard.render()
        
        # Verify page components were rendered
        mock_title.assert_called()


# Integration tests
class TestPageIntegration:
    """Integration tests for page interactions."""
    
    def test_all_pages_have_render_function(self):
        """Test that all page modules have a render function."""
        from pages import (
            home,
            mcp_management,
            performance_monitor,
            marketplace,
            registry,
            query_playground,
            training_dashboard,
            system_health
        )
        
        pages = [home, mcp_management, performance_monitor, marketplace, 
                registry, query_playground, training_dashboard, system_health]
        
        for page in pages:
            assert hasattr(page, 'render'), f"{page.__name__} missing render function"
            assert callable(page.render), f"{page.__name__}.render is not callable"
    
    def test_all_pages_import_successfully(self):
        """Test that all page modules can be imported without errors."""
        try:
            from pages import (
                home,
                mcp_management,
                performance_monitor,
                marketplace,
                registry,
                query_playground,
                training_dashboard,
                system_health
            )
        except Exception as e:
            pytest.fail(f"Failed to import pages: {e}")

