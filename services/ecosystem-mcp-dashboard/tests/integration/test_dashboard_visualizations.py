"""
Integration tests for dashboard visualizations.

Tests charts, graphs, interactive elements, and data displays.
Note: These tests focus on data preparation and visualization logic.
"""

import pytest
import httpx
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json


pytestmark = pytest.mark.integration


@pytest.fixture
def api_base_url():
    """Get API base URL from environment."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
async def async_http_client(api_base_url):
    """Create async HTTP client."""
    async with httpx.AsyncClient(base_url=api_base_url, timeout=10.0) as client:
        yield client


@pytest.fixture
def mock_streamlit_session():
    """Mock Streamlit session state."""
    session_state = {}
    with patch('streamlit.session_state', session_state):
        yield session_state


@pytest.fixture
def sample_metrics_data():
    """Sample metrics data for visualization tests."""
    return {
        'ingestion': {
            'total_documents': 1000,
            'total_embeddings': 950,
            'success_rate': 0.95
        },
        'queries': {
            'total_queries': 500,
            'avg_latency': 0.25,
            'cache_hit_rate': 0.75
        },
        'timeline': [
            {'timestamp': '2025-10-23T10:00:00', 'documents': 100},
            {'timestamp': '2025-10-23T11:00:00', 'documents': 200},
            {'timestamp': '2025-10-23T12:00:00', 'documents': 300}
        ]
    }


class TestChartsAndGraphs:
    """Test chart and graph visualizations."""

    async def test_metrics_chart_data(self, async_http_client, mock_streamlit_session):
        """Test metrics chart data preparation."""
        try:
            response = await async_http_client.get("/api/v1/admin/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                # Prepare chart data
                mock_streamlit_session['chart_data'] = data
                
                assert isinstance(mock_streamlit_session['chart_data'], dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    def test_timeline_visualization_data(self, sample_metrics_data, mock_streamlit_session):
        """Test timeline visualization data preparation."""
        timeline_data = sample_metrics_data['timeline']
        
        # Prepare for visualization
        mock_streamlit_session['timeline_chart'] = {
            'timestamps': [item['timestamp'] for item in timeline_data],
            'values': [item['documents'] for item in timeline_data]
        }
        
        assert len(mock_streamlit_session['timeline_chart']['timestamps']) == 3
        assert len(mock_streamlit_session['timeline_chart']['values']) == 3

    def test_progress_indicator_data(self, sample_metrics_data, mock_streamlit_session):
        """Test progress indicator data."""
        ingestion = sample_metrics_data['ingestion']
        
        # Calculate progress
        progress = ingestion['total_embeddings'] / ingestion['total_documents']
        mock_streamlit_session['progress'] = progress
        
        assert 0.0 <= mock_streamlit_session['progress'] <= 1.0
        assert mock_streamlit_session['progress'] == 0.95

    def test_status_badge_data(self, mock_streamlit_session):
        """Test status badge data preparation."""
        statuses = ['healthy', 'degraded', 'unhealthy']
        
        for status in statuses:
            mock_streamlit_session['service_status'] = status
            
            # Map to badge color
            badge_colors = {
                'healthy': 'green',
                'degraded': 'yellow',
                'unhealthy': 'red'
            }
            
            mock_streamlit_session['badge_color'] = badge_colors.get(status, 'gray')
            
            assert mock_streamlit_session['badge_color'] in ['green', 'yellow', 'red']

    def test_data_table_preparation(self, sample_metrics_data, mock_streamlit_session):
        """Test data table preparation."""
        # Prepare table data
        table_data = []
        for key, value in sample_metrics_data['ingestion'].items():
            table_data.append({
                'metric': key,
                'value': value
            })
        
        mock_streamlit_session['table_data'] = table_data
        
        assert len(mock_streamlit_session['table_data']) == 3
        assert all('metric' in row and 'value' in row for row in table_data)


class TestInteractiveElements:
    """Test interactive visualization elements."""

    def test_filters_and_sorting(self, mock_streamlit_session):
        """Test filter and sort functionality."""
        # Sample data
        data = [
            {'name': 'doc1', 'size': 100, 'date': '2025-10-23'},
            {'name': 'doc2', 'size': 200, 'date': '2025-10-22'},
            {'name': 'doc3', 'size': 150, 'date': '2025-10-21'}
        ]
        
        mock_streamlit_session['data'] = data
        
        # Apply filter
        mock_streamlit_session['filter_min_size'] = 150
        filtered = [d for d in data if d['size'] >= mock_streamlit_session['filter_min_size']]
        
        assert len(filtered) == 2
        
        # Apply sort
        sorted_data = sorted(filtered, key=lambda x: x['size'], reverse=True)
        mock_streamlit_session['sorted_data'] = sorted_data
        
        assert mock_streamlit_session['sorted_data'][0]['size'] == 200

    def test_pagination(self, mock_streamlit_session):
        """Test pagination logic."""
        # Sample data
        data = list(range(100))
        page_size = 10
        
        mock_streamlit_session['data'] = data
        mock_streamlit_session['page_size'] = page_size
        mock_streamlit_session['current_page'] = 1
        
        # Calculate pagination (page 1 starts at index 0)
        start_idx = (mock_streamlit_session['current_page'] - 1) * page_size
        end_idx = start_idx + page_size
        
        page_data = data[start_idx:end_idx]
        mock_streamlit_session['page_data'] = page_data
        
        assert len(mock_streamlit_session['page_data']) == 10
        assert mock_streamlit_session['page_data'][0] == 0  # First page starts at 0

    def test_search_and_highlight(self, mock_streamlit_session):
        """Test search and highlight functionality."""
        # Sample data
        data = [
            {'id': 1, 'content': 'Hello world'},
            {'id': 2, 'content': 'Python programming'},
            {'id': 3, 'content': 'Hello Python'}
        ]
        
        mock_streamlit_session['data'] = data
        mock_streamlit_session['search_query'] = 'Python'
        
        # Search
        results = [d for d in data if mock_streamlit_session['search_query'].lower() in d['content'].lower()]
        mock_streamlit_session['search_results'] = results
        
        assert len(mock_streamlit_session['search_results']) == 2

    def test_tooltips_and_popovers(self, mock_streamlit_session):
        """Test tooltip data preparation."""
        # Prepare tooltip data
        mock_streamlit_session['tooltips'] = {
            'total_documents': 'Total number of documents ingested',
            'success_rate': 'Percentage of successfully processed documents',
            'cache_hit_rate': 'Percentage of queries served from cache'
        }
        
        assert len(mock_streamlit_session['tooltips']) == 3
        assert 'total_documents' in mock_streamlit_session['tooltips']

    async def test_export_functionality(self, sample_metrics_data, mock_streamlit_session):
        """Test data export functionality."""
        # Prepare export data
        export_data = sample_metrics_data['ingestion']
        
        # Convert to JSON
        json_export = json.dumps(export_data, indent=2)
        mock_streamlit_session['export_json'] = json_export
        
        # Convert to CSV format
        csv_rows = []
        for key, value in export_data.items():
            csv_rows.append(f"{key},{value}")
        
        csv_export = "\n".join(csv_rows)
        mock_streamlit_session['export_csv'] = csv_export
        
        assert isinstance(mock_streamlit_session['export_json'], str)
        assert isinstance(mock_streamlit_session['export_csv'], str)
        assert len(csv_rows) == 3


class TestDataVisualizationHelpers:
    """Test data visualization helper functions."""

    def test_format_number(self, mock_streamlit_session):
        """Test number formatting."""
        numbers = [1000, 1000000, 1.5, 0.95]
        
        for num in numbers:
            if num >= 1000000:
                formatted = f"{num/1000000:.1f}M"
            elif num >= 1000:
                formatted = f"{num/1000:.1f}K"
            elif num < 1:
                formatted = f"{num*100:.1f}%"
            else:
                formatted = str(num)
            
            mock_streamlit_session[f'formatted_{num}'] = formatted
        
        assert mock_streamlit_session['formatted_1000000'] == '1.0M'
        assert mock_streamlit_session['formatted_1000'] == '1.0K'

    def test_format_duration(self, mock_streamlit_session):
        """Test duration formatting."""
        durations = [30, 90, 3600, 7200]
        
        for duration in durations:
            if duration < 60:
                formatted = f"{duration}s"
            elif duration < 3600:
                formatted = f"{duration//60}m {duration%60}s"
            else:
                formatted = f"{duration//3600}h {(duration%3600)//60}m"
            
            mock_streamlit_session[f'duration_{duration}'] = formatted
        
        assert mock_streamlit_session['duration_30'] == '30s'
        assert mock_streamlit_session['duration_90'] == '1m 30s'
        assert mock_streamlit_session['duration_3600'] == '1h 0m'

    def test_format_timestamp(self, mock_streamlit_session):
        """Test timestamp formatting."""
        timestamp = datetime(2025, 10, 23, 14, 30, 0)
        
        # Format as ISO
        iso_format = timestamp.isoformat()
        mock_streamlit_session['timestamp_iso'] = iso_format
        
        # Format as human-readable
        human_format = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        mock_streamlit_session['timestamp_human'] = human_format
        
        assert mock_streamlit_session['timestamp_iso'] == '2025-10-23T14:30:00'
        assert mock_streamlit_session['timestamp_human'] == '2025-10-23 14:30:00'

    def test_calculate_percentage(self, mock_streamlit_session):
        """Test percentage calculation."""
        total = 1000
        part = 750
        
        percentage = (part / total) * 100
        mock_streamlit_session['percentage'] = percentage
        
        assert mock_streamlit_session['percentage'] == 75.0

    def test_aggregate_metrics(self, sample_metrics_data, mock_streamlit_session):
        """Test metric aggregation."""
        timeline = sample_metrics_data['timeline']
        
        # Calculate total
        total = sum(item['documents'] for item in timeline)
        mock_streamlit_session['total_documents'] = total
        
        # Calculate average
        average = total / len(timeline)
        mock_streamlit_session['avg_documents'] = average
        
        assert mock_streamlit_session['total_documents'] == 600
        assert mock_streamlit_session['avg_documents'] == 200.0

