"""
Tests for Jira Connector
=========================

Unit tests for Jira API integration and pattern analysis.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.jira_connector import (
    JiraConnector,
    JiraTicket,
    JiraAnalytics
)


@pytest.fixture
def mock_log_client():
    """Create mock log collector client."""
    client = Mock()
    client.log_info = AsyncMock()
    client.log_error = AsyncMock()
    client.log_warning = AsyncMock()
    client.log_business_event = AsyncMock()
    return client


@pytest.fixture
def jira_connector(mock_log_client):
    """Create Jira connector with mock log client."""
    config = {
        'server': 'https://test.atlassian.net',
        'username': 'test@example.com',
        'api_token': 'test-token',
        'project_key': 'TEST'
    }
    return JiraConnector(config=config, log_client=mock_log_client)


@pytest.fixture
def sample_tickets():
    """Create sample Jira tickets for testing."""
    base_date = datetime.now() - timedelta(days=30)
    
    tickets = [
        JiraTicket(
            key="TEST-101",
            summary="Implement user authentication",
            description="Add secure login functionality",
            issue_type="Story",
            status="Done",
            priority="High",
            story_points=5.0,
            created=base_date,
            updated=base_date + timedelta(days=7),
            resolved=base_date + timedelta(days=7),
            assignee="john.doe",
            labels=["authentication", "security"],
            components=["backend"],
            sprint="Sprint 1"
        ),
        JiraTicket(
            key="TEST-102",
            summary="Fix password reset bug",
            description="Users can't reset passwords",
            issue_type="Bug",
            status="Done",
            priority="High",
            story_points=2.0,
            created=base_date + timedelta(days=1),
            updated=base_date + timedelta(days=3),
            resolved=base_date + timedelta(days=3),
            assignee="jane.smith",
            labels=["bug", "authentication"],
            components=["backend"],
            sprint="Sprint 1"
        ),
        JiraTicket(
            key="TEST-103",
            summary="Add user profile page",
            description="Create profile management UI",
            issue_type="Story",
            status="In Progress",
            priority="Medium",
            story_points=8.0,
            created=base_date + timedelta(days=5),
            updated=datetime.now(),
            resolved=None,
            assignee="john.doe",
            labels=["frontend", "ui"],
            components=["frontend"],
            sprint="Sprint 2"
        ),
        JiraTicket(
            key="TEST-104",
            summary="Database migration",
            description="Migrate to PostgreSQL",
            issue_type="Task",
            status="To Do",
            priority="Low",
            story_points=13.0,
            created=base_date + timedelta(days=10),
            updated=base_date + timedelta(days=10),
            resolved=None,
            assignee=None,
            labels=["database", "infrastructure"],
            components=["backend"],
            sprint="Sprint 2"
        ),
        JiraTicket(
            key="TEST-105",
            summary="Write API documentation",
            description="Document REST API endpoints",
            issue_type="Task",
            status="In Review",
            priority="Medium",
            story_points=3.0,
            created=base_date + timedelta(days=15),
            updated=datetime.now(),
            resolved=None,
            assignee="jane.smith",
            labels=["documentation"],
            components=["documentation"],
            sprint="Sprint 2"
        )
    ]
    
    return tickets


class TestJiraConnector:
    """Test suite for Jira Connector."""
    
    def test_connector_initialization(self, jira_connector):
        """Test connector initializes with config."""
        assert jira_connector is not None
        assert jira_connector.config['server'] == 'https://test.atlassian.net'
        assert jira_connector.config['project_key'] == 'TEST'
    
    def test_get_config_from_env(self, jira_connector):
        """Test configuration from environment variables."""
        config = jira_connector._get_config_from_env()
        assert 'server' in config
        assert 'username' in config
        assert 'api_token' in config
    
    @pytest.mark.asyncio
    async def test_fetch_tickets_returns_mock_data(self, jira_connector):
        """Test fetch_tickets returns mock data when Jira client unavailable."""
        tickets = await jira_connector.fetch_tickets('TEST', days_back=30)
        
        assert len(tickets) == 50  # Default mock count
        assert all(isinstance(t, JiraTicket) for t in tickets)
        assert all(t.key.startswith('TEST-') for t in tickets)
    
    @pytest.mark.asyncio
    async def test_analyze_ticket_patterns(self, jira_connector, sample_tickets):
        """Test ticket pattern analysis."""
        analytics = await jira_connector.analyze_ticket_patterns(sample_tickets)
        
        assert isinstance(analytics, JiraAnalytics)
        assert analytics.total_tickets == 5
        assert analytics.avg_ticket_size > 0  # Should have average story points
        assert 0 <= analytics.completion_rate <= 1  # Should be a percentage
        assert analytics.avg_cycle_time_days >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_empty_tickets(self, jira_connector):
        """Test analysis with empty ticket list."""
        analytics = await jira_connector.analyze_ticket_patterns([])
        
        assert analytics.total_tickets == 0
        assert analytics.avg_ticket_size == 0.0
        assert analytics.completion_rate == 0.0
        assert analytics.velocity == 0.0
    
    @pytest.mark.asyncio
    async def test_completion_rate_calculation(self, jira_connector, sample_tickets):
        """Test completion rate is calculated correctly."""
        analytics = await jira_connector.analyze_ticket_patterns(sample_tickets)
        
        # 2 out of 5 tickets are Done
        expected_completion_rate = 2 / 5
        assert analytics.completion_rate == pytest.approx(expected_completion_rate, rel=0.01)
    
    @pytest.mark.asyncio
    async def test_velocity_calculation(self, jira_connector, sample_tickets):
        """Test velocity calculation per sprint."""
        analytics = await jira_connector.analyze_ticket_patterns(sample_tickets)
        
        # Sprint 1: 5 + 2 = 7 points
        # Sprint 2: 8 + 13 + 3 = 24 points
        # Average: (7 + 24) / 2 = 15.5
        assert analytics.velocity > 0
    
    @pytest.mark.asyncio
    async def test_status_distribution(self, jira_connector, sample_tickets):
        """Test status distribution is calculated."""
        analytics = await jira_connector.analyze_ticket_patterns(sample_tickets)
        
        assert 'Done' in analytics.status_distribution
        assert 'In Progress' in analytics.status_distribution
        assert 'To Do' in analytics.status_distribution
        assert analytics.status_distribution['Done'] == 2
        assert analytics.status_distribution['In Progress'] == 1
    
    @pytest.mark.asyncio
    async def test_common_labels_extraction(self, jira_connector, sample_tickets):
        """Test common labels are identified."""
        analytics = await jira_connector.analyze_ticket_patterns(sample_tickets)
        
        assert len(analytics.common_labels) > 0
        # 'authentication' appears in 2 tickets, should be in common labels
        assert 'authentication' in analytics.common_labels
    
    @pytest.mark.asyncio
    async def test_bottleneck_identification(self, jira_connector):
        """Test bottleneck identification."""
        # Create tickets where > 20% are in "In Progress"
        tickets = []
        for i in range(10):
            status = "In Progress" if i < 3 else "Done"
            tickets.append(JiraTicket(
                key=f"TEST-{i}",
                summary=f"Ticket {i}",
                description="Test",
                issue_type="Story",
                status=status,
                priority="Medium",
                story_points=5.0,
                created=datetime.now() - timedelta(days=10),
                updated=datetime.now(),
                resolved=datetime.now() if status == "Done" else None,
                assignee="test",
                labels=[],
                components=[],
                sprint="Sprint 1"
            ))
        
        analytics = await jira_connector.analyze_ticket_patterns(tickets)
        
        # "In Progress" has 3/10 = 30% of tickets, should be a bottleneck
        assert "In Progress" in analytics.bottlenecks
    
    def test_generate_mock_tickets(self, jira_connector):
        """Test mock ticket generation."""
        tickets = jira_connector._generate_mock_tickets('TEST', 20)
        
        assert len(tickets) == 20
        assert all(t.key.startswith('TEST-') for t in tickets)
        assert all(t.story_points is not None for t in tickets)
        assert all(t.sprint is not None for t in tickets)
    
    @pytest.mark.asyncio
    async def test_get_sprint_metrics(self, jira_connector):
        """Test sprint metrics retrieval."""
        metrics = await jira_connector.get_sprint_metrics('TEST', sprint_name='Sprint 1')
        
        assert 'sprint' in metrics
        assert 'total_tickets' in metrics
        assert 'story_points_completed' in metrics
        assert 'completion_rate' in metrics
        assert metrics['sprint'] == 'Sprint 1'
    
    @pytest.mark.asyncio
    async def test_logging_integration(self, jira_connector, mock_log_client):
        """Test that operations are logged."""
        await jira_connector.fetch_tickets('TEST')
        
        # Should log warning about Jira client not initialized
        mock_log_client.log_warning.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

