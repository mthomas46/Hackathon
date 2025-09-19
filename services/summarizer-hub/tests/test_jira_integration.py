"""Unit Tests for Jira Integration in Summarizer Hub Service.

This module contains unit tests for Jira ticket creation and management functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from main import JiraClient, SimpleSummarizer


class TestJiraClient:
    """Test cases for JiraClient functionality."""

    @pytest.fixture
    def jira_client(self):
        """Create JiraClient instance for testing."""
        return JiraClient(
            base_url="https://test.atlassian.net",
            username="test@example.com",
            api_token="test_token"
        )

    @pytest.fixture
    def sample_suggested_tickets(self) -> List[Dict[str, Any]]:
        """Create sample suggested tickets for testing."""
        return [
            {
                "priority": "High",
                "issue_type": "Task",
                "summary": "📋 Documentation Consolidation Required",
                "description": "**Consolidation needed**\n\nMultiple similar documents found",
                "labels": ["documentation", "consolidation"],
                "components": ["Technical Writing"],
                "epic_link": "Documentation Quality Initiative"
            },
            {
                "priority": "Medium",
                "issue_type": "Bug",
                "summary": "✨ Improve Documentation Quality",
                "description": "**Quality improvements needed**\n\nDocumentation clarity issues detected",
                "labels": ["documentation", "quality"],
                "components": ["Quality Assurance"]
            }
        ]

    def test_jira_client_initialization(self):
        """Test JiraClient initialization."""
        client = JiraClient()
        assert client.base_url == "https://your-domain.atlassian.net"
        assert not client.is_configured()

        configured_client = JiraClient(
            base_url="https://test.atlassian.net",
            username="test@example.com",
            api_token="test_token"
        )
        assert configured_client.is_configured()

    def test_create_auth_header(self, jira_client):
        """Test Basic Auth header creation."""
        # Test with valid credentials
        assert jira_client.auth_header.startswith("Basic ")

        # Test with missing credentials
        empty_client = JiraClient()
        assert empty_client.auth_header == ""

    @pytest.mark.asyncio
    async def test_create_issue_success(self, jira_client):
        """Test successful Jira issue creation."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "key": "DOC-123",
                "id": "12345",
                "self": "https://test.atlassian.net/rest/api/2/issue/12345"
            }
            mock_client.post.return_value = mock_response

            result = await jira_client.create_issue(
                project_key="DOC",
                summary="Test Issue",
                description="Test description",
                issue_type="Task",
                priority="High"
            )

            assert result["success"] is True
            assert result["issue_key"] == "DOC-123"
            assert result["issue_id"] == "12345"

    @pytest.mark.asyncio
    async def test_create_issue_failure(self, jira_client):
        """Test Jira issue creation failure."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock failed response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_client.post.return_value = mock_response

            result = await jira_client.create_issue(
                project_key="DOC",
                summary="Test Issue",
                description="Test description"
            )

            assert result["success"] is False
            assert "Bad Request" in result["error"]

    @pytest.mark.asyncio
    async def test_create_jira_tickets_from_suggestions_success(self, jira_client, sample_suggested_tickets):
        """Test creating multiple Jira tickets from suggestions."""
        with patch.object(jira_client, 'create_issue', new_callable=AsyncMock) as mock_create_issue:
            # Mock successful ticket creation
            mock_create_issue.side_effect = [
                {"success": True, "issue_key": "DOC-123"},
                {"success": True, "issue_key": "DOC-124"}
            ]

            result = await jira_client.create_jira_tickets_from_suggestions(
                sample_suggested_tickets, "DOC"
            )

            assert result["success"] is True
            assert result["tickets_created"] == 2
            assert result["tickets_failed"] == 0
            assert result["project_key"] == "DOC"
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_create_jira_tickets_from_suggestions_partial_failure(self, jira_client, sample_suggested_tickets):
        """Test creating Jira tickets with partial failures."""
        with patch.object(jira_client, 'create_issue', new_callable=AsyncMock) as mock_create_issue:
            # Mock mixed results
            mock_create_issue.side_effect = [
                {"success": True, "issue_key": "DOC-123"},
                {"success": False, "error": "Permission denied"}
            ]

            result = await jira_client.create_jira_tickets_from_suggestions(
                sample_suggested_tickets, "DOC"
            )

            assert result["success"] is True  # At least one succeeded
            assert result["tickets_created"] == 1
            assert result["tickets_failed"] == 1
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_create_jira_tickets_from_suggestions_not_configured(self):
        """Test creating tickets when Jira client is not configured."""
        unconfigured_client = JiraClient()  # No credentials

        result = await unconfigured_client.create_jira_tickets_from_suggestions(
            [{"summary": "Test"}], "DOC"
        )

        assert result["success"] is False
        assert "not configured" in result["error"]
        assert result["tickets_created"] == 0
        assert result["tickets_failed"] == 1

    @pytest.mark.asyncio
    async def test_create_jira_tickets_for_recommendations(self, jira_client):
        """Test creating tickets directly from recommendations."""
        recommendations = [
            {
                "type": "consolidation",
                "priority": "high",
                "description": "Multiple similar documents found"
            }
        ]

        with patch.object(jira_client, 'create_jira_tickets_from_suggestions', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                "success": True,
                "tickets_created": 1,
                "tickets_failed": 0
            }

            result = await jira_client.create_jira_tickets_for_recommendations(
                recommendations, None, "DOC"
            )

            assert mock_create.called
            assert result["success"] is True
            assert result["tickets_created"] == 1


class TestJiraIntegrationWithSummarizer:
    """Integration tests for Jira functionality with SimpleSummarizer."""

    @pytest.fixture
    def summarizer(self):
        """Create SimpleSummarizer instance for testing."""
        return SimpleSummarizer()

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            {
                "id": "doc1",
                "title": "API Documentation",
                "content": "This document covers API endpoints and usage patterns"
            },
            {
                "id": "doc2",
                "title": "Setup Guide",
                "content": "Installation and setup instructions"
            }
        ]

    @pytest.mark.asyncio
    async def test_generate_recommendations_with_jira_creation_disabled(self, summarizer, sample_documents):
        """Test recommendations generation without Jira ticket creation."""
        result = await summarizer.generate_recommendations(
            documents=sample_documents,
            include_jira_suggestions=False,
            create_jira_tickets=False
        )

        assert "jira_ticket_creation" in result
        assert result["jira_ticket_creation"] == {}
        assert "suggested_jira_tickets" not in result or result["suggested_jira_tickets"] == []

    @pytest.mark.asyncio
    async def test_generate_recommendations_with_jira_suggestions_only(self, summarizer, sample_documents):
        """Test recommendations generation with Jira suggestions but no creation."""
        result = await summarizer.generate_recommendations(
            documents=sample_documents,
            include_jira_suggestions=True,
            create_jira_tickets=False
        )

        assert "suggested_jira_tickets" in result
        assert "jira_ticket_creation" in result
        assert result["jira_ticket_creation"] == {}

    @pytest.mark.asyncio
    async def test_generate_recommendations_with_jira_creation_enabled(self, summarizer, sample_documents):
        """Test recommendations generation with Jira ticket creation enabled."""
        with patch('main.jira_client', new_callable=AsyncMock) as mock_jira_client:
            mock_jira_client.create_jira_tickets_from_suggestions.return_value = {
                "success": True,
                "tickets_created": 1,
                "tickets_failed": 0,
                "results": [{"status": "created"}]
            }

            result = await summarizer.generate_recommendations(
                documents=sample_documents,
                include_jira_suggestions=True,
                create_jira_tickets=True,
                jira_project_key="DOC"
            )

            assert mock_jira_client.create_jira_tickets_from_suggestions.called
            assert "jira_ticket_creation" in result
            assert result["jira_ticket_creation"]["success"] is True
            assert result["jira_ticket_creation"]["tickets_created"] == 1

    @pytest.mark.asyncio
    async def test_generate_recommendations_with_jira_creation_failure(self, summarizer, sample_documents):
        """Test recommendations generation when Jira ticket creation fails."""
        with patch('main.jira_client', new_callable=AsyncMock) as mock_jira_client:
            mock_jira_client.create_jira_tickets_from_suggestions.return_value = {
                "success": False,
                "error": "Jira API error",
                "tickets_created": 0,
                "tickets_failed": 1
            }

            result = await summarizer.generate_recommendations(
                documents=sample_documents,
                include_jira_suggestions=True,
                create_jira_tickets=True
            )

            assert "jira_ticket_creation" in result
            assert result["jira_ticket_creation"]["success"] is False
            assert "error" in result["jira_ticket_creation"]


class TestJiraTicketGeneration:
    """Test cases for Jira ticket suggestion generation."""

    @pytest.fixture
    def summarizer(self):
        """Create SimpleSummarizer instance for testing."""
        return SimpleSummarizer()

    def test_generate_jira_ticket_suggestions_empty_recommendations(self, summarizer):
        """Test Jira ticket generation with no recommendations."""
        suggestions = summarizer._generate_jira_ticket_suggestions([], [])

        assert suggestions == []

    def test_generate_jira_ticket_suggestions_with_recommendations(self, summarizer):
        """Test Jira ticket generation with various recommendation types."""
        recommendations = [
            {
                "type": "consolidation",
                "priority": "high",
                "description": "Multiple similar documents found",
                "confidence_score": 0.9
            },
            {
                "type": "quality",
                "priority": "medium",
                "description": "Documentation quality issues detected",
                "confidence_score": 0.7
            },
            {
                "type": "outdated",
                "priority": "high",
                "description": "Outdated content found",
                "confidence_score": 0.8
            }
        ]

        suggestions = summarizer._generate_jira_ticket_suggestions(recommendations, [])

        assert len(suggestions) > 0
        # Should generate at least one high-priority ticket for critical issues
        high_priority_tickets = [s for s in suggestions if s["priority"] in ["Critical", "High"]]
        assert len(high_priority_tickets) >= 1

        # Check ticket structure
        for ticket in suggestions:
            assert "priority" in ticket
            assert "issue_type" in ticket
            assert "summary" in ticket
            assert "description" in ticket
            assert "labels" in ticket
            assert "epic_link" in ticket

    def test_generate_jira_ticket_suggestions_consolidation_focus(self, summarizer):
        """Test Jira ticket generation focused on consolidation recommendations."""
        recommendations = [
            {
                "type": "consolidation",
                "priority": "high",
                "description": "Multiple consolidation opportunities found",
                "confidence_score": 0.9
            },
            {
                "type": "consolidation",
                "priority": "medium",
                "description": "Additional consolidation needed",
                "confidence_score": 0.8
            }
        ]

        suggestions = summarizer._generate_jira_ticket_suggestions(recommendations, [])

        # Should include consolidation-focused tickets
        consolidation_tickets = [s for s in suggestions if "consolidation" in s["summary"].lower()]
        assert len(consolidation_tickets) >= 1

    def test_generate_jira_ticket_suggestions_quality_focus(self, summarizer):
        """Test Jira ticket generation focused on quality recommendations."""
        recommendations = [
            {
                "type": "quality",
                "priority": "medium",
                "description": "Quality improvements needed",
                "confidence_score": 0.7
            },
            {
                "type": "quality",
                "priority": "high",
                "description": "Critical quality issues found",
                "confidence_score": 0.9
            }
        ]

        suggestions = summarizer._generate_jira_ticket_suggestions(recommendations, [])

        # Should include quality-focused tickets
        quality_tickets = [s for s in suggestions if "quality" in s["summary"].lower()]
        assert len(quality_tickets) >= 1

    def test_generate_jira_ticket_suggestions_priority_sorting(self, summarizer):
        """Test that Jira tickets are sorted by priority."""
        recommendations = [
            {"type": "quality", "priority": "low", "description": "Minor issue"},
            {"type": "consolidation", "priority": "high", "description": "Major issue"},
            {"type": "outdated", "priority": "medium", "description": "Medium issue"}
        ]

        suggestions = summarizer._generate_jira_ticket_suggestions(recommendations, [])

        # Check that higher priority tickets come first
        priorities = [s["priority"] for s in suggestions]
        # Should be sorted with Critical/High first, then Medium, then Low
        priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        sorted_priorities = sorted(priorities, key=lambda x: priority_order.get(x, 4))

        # If we have different priorities, they should be in order
        if len(set(priorities)) > 1:
            assert priorities == sorted_priorities
