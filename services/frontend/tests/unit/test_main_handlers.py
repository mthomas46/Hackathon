"""Tests for Main UI Handlers"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.responses import HTMLResponse

from services.frontend.modules.ui_handlers.main_handlers import MainUIHandlers


class TestMainUIHandlers:
    """Test cases for MainUIHandlers."""

    @pytest.fixture
    def handlers(self):
        """Create MainUIHandlers instance."""
        return MainUIHandlers()

    def test_handle_index_success(self, handlers):
        """Test successful index page rendering."""
        with patch('services.frontend.modules.ui_handlers.main_handlers.render_index') as mock_render, \
             patch('services.frontend.modules.ui_handlers.main_handlers.create_html_response') as mock_response:

            mock_render.return_value = "<html>Test</html>"
            mock_response.return_value = HTMLResponse(content="<html>Test</html>")

            result = handlers.handle_index()

            mock_render.assert_called_once()
            mock_response.assert_called_once_with("<html>Test</html>", "LLM Documentation Ecosystem")
            assert isinstance(result, HTMLResponse)

    def test_handle_index_error(self, handlers):
        """Test index page rendering with error."""
        with patch('services.frontend.modules.ui_handlers.main_handlers.render_index') as mock_render, \
             patch('services.frontend.modules.ui_handlers.main_handlers.handle_frontend_error') as mock_error:

            mock_render.side_effect = Exception("Render failed")
            mock_error.return_value = HTMLResponse(content="Error page")

            result = handlers.handle_index()

            mock_render.assert_called_once()
            mock_error.assert_called_once()
            assert isinstance(result, HTMLResponse)

    @pytest.mark.asyncio
    async def test_handle_owner_coverage_success(self, handlers):
        """Test successful owner coverage page rendering."""
        with patch('services.frontend.modules.ui_handlers.main_handlers.get_frontend_clients') as mock_clients, \
             patch('services.frontend.modules.ui_handlers.main_handlers.render_owner_coverage_table') as mock_render, \
             patch('services.frontend.modules.ui_handlers.main_handlers.create_html_response') as mock_response:

            mock_client_instance = AsyncMock()
            mock_clients.return_value = mock_client_instance
            mock_render.return_value = "<table>Test</table>"
            mock_response.return_value = HTMLResponse(content="<table>Test</table>")

            result = await handlers.handle_owner_coverage()

            mock_clients.assert_called_once()
            mock_render.assert_called_once()
            mock_response.assert_called_once_with("<table>Test</table>", "Owner Coverage Report")
            assert isinstance(result, HTMLResponse)

    @pytest.mark.asyncio
    async def test_handle_owner_coverage_error(self, handlers):
        """Test owner coverage page rendering with error."""
        with patch('services.frontend.modules.ui_handlers.main_handlers.get_frontend_clients') as mock_clients, \
             patch('services.frontend.modules.ui_handlers.main_handlers.handle_frontend_error') as mock_error:

            mock_clients.side_effect = Exception("Client error")
            mock_error.return_value = HTMLResponse(content="Error page")

            result = await handlers.handle_owner_coverage()

            mock_clients.assert_called_once()
            mock_error.assert_called_once()
            assert isinstance(result, HTMLResponse)

    @pytest.mark.asyncio
    async def test_handle_topics_success(self, handlers):
        """Test successful topics page rendering."""
        with patch('services.frontend.modules.ui_handlers.main_handlers.get_frontend_clients') as mock_clients, \
             patch('services.frontend.modules.ui_handlers.main_handlers.render_topics_html') as mock_render, \
             patch('services.frontend.modules.ui_handlers.main_handlers.create_html_response') as mock_response:

            mock_client_instance = AsyncMock()
            mock_clients.return_value = mock_client_instance
            mock_render.return_value = "<div>Topics</div>"
            mock_response.return_value = HTMLResponse(content="<div>Topics</div>")

            result = await handlers.handle_topics()

            mock_clients.assert_called_once()
            mock_render.assert_called_once()
            mock_response.assert_called_once_with("<div>Topics</div>", "Topic Analysis")
            assert isinstance(result, HTMLResponse)

    @pytest.mark.asyncio
    async def test_handle_search_success(self, handlers):
        """Test successful search page rendering."""
        query = "test query"
        page = 1

        with patch('services.frontend.modules.ui_handlers.main_handlers.sanitize_input') as mock_sanitize, \
             patch('services.frontend.modules.ui_handlers.main_handlers.get_frontend_clients') as mock_clients, \
             patch('services.frontend.modules.ui_handlers.main_handlers.render_search_results') as mock_render, \
             patch('services.frontend.modules.ui_handlers.main_handlers.create_html_response') as mock_response:

            mock_sanitize.return_value = "sanitized query"
            mock_client_instance = AsyncMock()
            mock_clients.return_value = mock_client_instance
            mock_render.return_value = "<div>Search results</div>"
            mock_response.return_value = HTMLResponse(content="<div>Search results</div>")

            result = await handlers.handle_search(query, page)

            mock_sanitize.assert_called_once_with(query)
            mock_clients.assert_called_once()
            mock_render.assert_called_once()
            mock_response.assert_called_once_with("<div>Search results</div>", "Search Results - sanitized query")
            assert isinstance(result, HTMLResponse)

    @pytest.mark.asyncio
    async def test_handle_search_validation_error(self, handlers):
        """Test search with validation error."""
        query = ""  # Empty query should fail validation

        with patch('services.frontend.modules.ui_handlers.main_handlers.validate_frontend_request') as mock_validate, \
             patch('services.frontend.modules.ui_handlers.main_handlers.handle_frontend_error') as mock_error:

            mock_validate.return_value = (False, "Query is required")
            mock_error.return_value = HTMLResponse(content="Error page")

            result = await handlers.handle_search(query, 1)

            mock_validate.assert_called_once()
            mock_error.assert_called_once()
            assert isinstance(result, HTMLResponse)

    @pytest.mark.asyncio
    async def test_handle_report_success(self, handlers):
        """Test successful report page rendering."""
        report_id = "test-report-123"

        with patch('services.frontend.modules.ui_handlers.main_handlers.validate_frontend_request') as mock_validate, \
             patch('services.frontend.modules.ui_handlers.main_handlers.get_frontend_clients') as mock_clients, \
             patch('services.frontend.modules.ui_handlers.main_handlers.render_report_page') as mock_render, \
             patch('services.frontend.modules.ui_handlers.main_handlers.create_html_response') as mock_response:

            mock_validate.return_value = (True, None)
            mock_client_instance = AsyncMock()
            mock_clients.return_value = mock_client_instance
            mock_render.return_value = "<div>Report content</div>"
            mock_response.return_value = HTMLResponse(content="<div>Report content</div>")

            result = await handlers.handle_report(report_id)

            mock_validate.assert_called_once()
            mock_clients.assert_called_once()
            mock_render.assert_called_once()
            mock_response.assert_called_once_with("<div>Report content</div>", f"Report: {report_id}")
            assert isinstance(result, HTMLResponse)

    @pytest.mark.asyncio
    async def test_handle_consolidation_success(self, handlers):
        """Test successful consolidation page rendering."""
        with patch('services.frontend.modules.ui_handlers.main_handlers.get_frontend_clients') as mock_clients, \
             patch('services.frontend.modules.ui_handlers.main_handlers.render_consolidation_list') as mock_render, \
             patch('services.frontend.modules.ui_handlers.main_handlers.create_html_response') as mock_response:

            mock_client_instance = AsyncMock()
            mock_clients.return_value = mock_client_instance
            mock_render.return_value = "<ul>Consolidation list</ul>"
            mock_response.return_value = HTMLResponse(content="<ul>Consolidation list</ul>")

            result = await handlers.handle_consolidation()

            mock_clients.assert_called_once()
            mock_render.assert_called_once()
            mock_response.assert_called_once_with("<ul>Consolidation list</ul>", "Document Consolidation")
            assert isinstance(result, HTMLResponse)
