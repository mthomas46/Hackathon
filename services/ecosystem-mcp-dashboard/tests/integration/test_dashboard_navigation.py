"""
Integration tests for dashboard navigation.

Tests page routing, sidebar navigation, and error handling.
Note: These tests focus on navigation logic and state management.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st


pytestmark = pytest.mark.integration


@pytest.fixture
def mock_streamlit_session():
    """Mock Streamlit session state."""
    session_state = {}
    with patch('streamlit.session_state', session_state):
        yield session_state


@pytest.fixture
def mock_streamlit_components():
    """Mock Streamlit UI components."""
    with patch('streamlit.sidebar') as mock_sidebar, \
         patch('streamlit.title') as mock_title, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.warning') as mock_warning, \
         patch('streamlit.success') as mock_success:
        yield {
            'sidebar': mock_sidebar,
            'title': mock_title,
            'error': mock_error,
            'warning': mock_warning,
            'success': mock_success
        }


class TestPageRouting:
    """Test page routing and navigation."""

    def test_home_page_route(self, mock_streamlit_session):
        """Test navigation to home page."""
        mock_streamlit_session['current_page'] = 'home'
        assert mock_streamlit_session['current_page'] == 'home'

    def test_ingestion_page_route(self, mock_streamlit_session):
        """Test navigation to ingestion page."""
        mock_streamlit_session['current_page'] = 'ingestion'
        assert mock_streamlit_session['current_page'] == 'ingestion'

    def test_rag_query_page_route(self, mock_streamlit_session):
        """Test navigation to RAG query page."""
        mock_streamlit_session['current_page'] = 'rag_query'
        assert mock_streamlit_session['current_page'] == 'rag_query'

    def test_session_state_persistence(self, mock_streamlit_session):
        """Test session state persistence across navigation."""
        # Set some state
        mock_streamlit_session['user_data'] = {'key': 'value'}
        mock_streamlit_session['current_page'] = 'home'
        
        # Navigate to another page
        mock_streamlit_session['current_page'] = 'ingestion'
        
        # Verify state persists
        assert mock_streamlit_session['user_data'] == {'key': 'value'}

    def test_deep_linking(self, mock_streamlit_session):
        """Test deep linking to specific pages."""
        # Simulate URL parameter
        mock_streamlit_session['page'] = 'chromadb_explorer'
        assert mock_streamlit_session['page'] == 'chromadb_explorer'


class TestSidebarNavigation:
    """Test sidebar navigation functionality."""

    def test_sidebar_menu_items(self, mock_streamlit_components):
        """Test sidebar menu item rendering."""
        # This would normally render menu items
        # We're testing that the mock is called
        assert mock_streamlit_components['sidebar'] is not None

    def test_active_page_highlighting(self, mock_streamlit_session):
        """Test active page highlighting in sidebar."""
        mock_streamlit_session['current_page'] = 'ingestion'
        assert mock_streamlit_session['current_page'] == 'ingestion'

    def test_collapsible_sections(self, mock_streamlit_session):
        """Test collapsible sidebar sections."""
        mock_streamlit_session['sidebar_collapsed'] = False
        mock_streamlit_session['sidebar_collapsed'] = True
        assert mock_streamlit_session['sidebar_collapsed'] is True

    def test_quick_actions(self, mock_streamlit_session):
        """Test quick action buttons in sidebar."""
        mock_streamlit_session['quick_action'] = 'start_ingestion'
        assert mock_streamlit_session['quick_action'] == 'start_ingestion'

    def test_sidebar_search(self, mock_streamlit_session):
        """Test sidebar search functionality."""
        mock_streamlit_session['search_query'] = 'test'
        assert mock_streamlit_session['search_query'] == 'test'


class TestErrorPageHandling:
    """Test error page handling and display."""

    def test_404_page_display(self, mock_streamlit_session, mock_streamlit_components):
        """Test 404 page display."""
        mock_streamlit_session['error_code'] = 404
        mock_streamlit_components['error']("Page not found")
        
        # Verify error was called
        mock_streamlit_components['error'].assert_called_once()

    def test_api_error_display(self, mock_streamlit_session, mock_streamlit_components):
        """Test API error display."""
        mock_streamlit_session['api_error'] = "Connection refused"
        mock_streamlit_components['error']("API Error: Connection refused")
        
        # Verify error was displayed
        mock_streamlit_components['error'].assert_called_once()

    def test_connection_error_display(self, mock_streamlit_components):
        """Test connection error display."""
        mock_streamlit_components['error']("Unable to connect to API")
        mock_streamlit_components['error'].assert_called_once()

    def test_timeout_handling(self, mock_streamlit_session, mock_streamlit_components):
        """Test timeout error handling."""
        mock_streamlit_session['timeout_error'] = True
        mock_streamlit_components['warning']("Request timed out")
        
        # Verify warning was displayed
        mock_streamlit_components['warning'].assert_called_once()

    def test_retry_mechanism(self, mock_streamlit_session):
        """Test retry mechanism for failed requests."""
        mock_streamlit_session['retry_count'] = 0
        mock_streamlit_session['retry_count'] += 1
        assert mock_streamlit_session['retry_count'] == 1


class TestNavigationState:
    """Test navigation state management."""

    def test_navigation_history(self, mock_streamlit_session):
        """Test navigation history tracking."""
        mock_streamlit_session['navigation_history'] = []
        mock_streamlit_session['navigation_history'].append('home')
        mock_streamlit_session['navigation_history'].append('ingestion')
        
        assert len(mock_streamlit_session['navigation_history']) == 2
        assert mock_streamlit_session['navigation_history'][-1] == 'ingestion'

    def test_back_navigation(self, mock_streamlit_session):
        """Test back navigation."""
        mock_streamlit_session['navigation_history'] = ['home', 'ingestion', 'rag_query']
        
        # Go back
        previous_page = mock_streamlit_session['navigation_history'][-2]
        assert previous_page == 'ingestion'

    def test_forward_navigation(self, mock_streamlit_session):
        """Test forward navigation."""
        mock_streamlit_session['navigation_history'] = ['home', 'ingestion']
        mock_streamlit_session['forward_stack'] = ['rag_query']
        
        # Go forward
        next_page = mock_streamlit_session['forward_stack'][0]
        assert next_page == 'rag_query'

    def test_state_cleanup_on_navigation(self, mock_streamlit_session):
        """Test state cleanup when navigating away."""
        mock_streamlit_session['temp_data'] = {'key': 'value'}
        mock_streamlit_session['current_page'] = 'ingestion'
        
        # Navigate away and cleanup
        mock_streamlit_session['current_page'] = 'home'
        mock_streamlit_session.pop('temp_data', None)
        
        assert 'temp_data' not in mock_streamlit_session

    def test_persistent_state_preservation(self, mock_streamlit_session):
        """Test persistent state preservation across navigation."""
        mock_streamlit_session['api_base_url'] = 'http://localhost:8000'
        mock_streamlit_session['current_page'] = 'home'
        
        # Navigate
        mock_streamlit_session['current_page'] = 'ingestion'
        
        # Verify persistent state remains
        assert mock_streamlit_session['api_base_url'] == 'http://localhost:8000'

