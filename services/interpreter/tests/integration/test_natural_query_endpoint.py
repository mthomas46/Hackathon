"""
Integration tests for the /natural-query endpoint with WorkflowLogger.

These tests verify the enhanced v2.0 natural language query processing
with full workflow tracking and logging integration.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


@pytest.fixture
def mock_workflow_logger():
    """Mock WorkflowLogger for testing."""
    logger = MagicMock()
    logger.log_workflow_start = AsyncMock()
    logger.log_workflow_step = AsyncMock()
    logger.log_workflow_complete = AsyncMock()
    logger.log_error = AsyncMock()
    return logger


@pytest.fixture
def client_with_mocked_logger(mock_workflow_logger):
    """Create test client with mocked WorkflowLogger."""
    with patch('services.interpreter.main.workflow_logger', mock_workflow_logger):
        from services.interpreter.main import app
        with TestClient(app) as client:
            yield client, mock_workflow_logger


class TestNaturalQueryEndpoint:
    """Test suite for /natural-query endpoint."""
    
    def test_feature_planning_query(self, client_with_mocked_logger):
        """Test that feature planning queries are correctly identified."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={
                "query": "I want to plan a new authentication feature for our mobile app",
                "user_id": "test-user-123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "workflow_id" in data
        assert data["workflow_id"].startswith("wf-")
        assert "interpreted_intent" in data
        assert data["interpreted_intent"]["type"] == "feature_planning"
        assert data["confidence"] >= 0.90
        
        # Verify entity extraction
        assert data["entities"]["feature_type"] == "authentication"
        assert data["entities"]["platform"] == "mobile"
        
        # Verify next step
        assert data["next_step"] == "orchestrator"
        
        # Verify logging was called
        mock_logger.log_workflow_start.assert_called_once()
        mock_logger.log_workflow_complete.assert_called_once()
        
    def test_document_analysis_query(self, client_with_mocked_logger):
        """Test that analysis queries are correctly identified."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={
                "query": "Analyze the documentation for security issues"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["interpreted_intent"]["type"] == "document_analysis"
        assert data["confidence"] >= 0.80
        
    def test_team_size_extraction(self, client_with_mocked_logger):
        """Test that team size is correctly extracted."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={
                "query": "Plan a payment dashboard for a team of 8 developers"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["entities"]["feature_type"] == "payment"
        assert data["entities"]["team_size"] == 8
        
    def test_empty_query_validation(self, client_with_mocked_logger):
        """Test that empty queries are rejected."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={"query": ""}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
        assert "workflow_id" in data["detail"]
        
        # Verify error was logged
        mock_logger.log_error.assert_called_once()
        
    def test_workflow_id_uniqueness(self, client_with_mocked_logger):
        """Test that each request gets a unique workflow_id."""
        client, mock_logger = client_with_mocked_logger
        
        response1 = client.post(
            "/natural-query",
            json={"query": "Plan authentication"}
        )
        response2 = client.post(
            "/natural-query",
            json={"query": "Plan dashboard"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        wf_id1 = response1.json()["workflow_id"]
        wf_id2 = response2.json()["workflow_id"]
        
        assert wf_id1 != wf_id2
        
    def test_processing_time_tracking(self, client_with_mocked_logger):
        """Test that processing time is tracked."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={"query": "Create a dashboard"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] > 0
        assert isinstance(data["processing_time_ms"], (int, float))
        
    def test_timestamp_included(self, client_with_mocked_logger):
        """Test that timestamp is included in response."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan authentication"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(data["timestamp"])
        
    def test_logging_flag(self, client_with_mocked_logger):
        """Test that logged flag indicates WorkflowLogger is active."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan dashboard"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["logged"] is True
        
    def test_platform_detection(self, client_with_mocked_logger):
        """Test that platform is correctly detected."""
        client, mock_logger = client_with_mocked_logger
        
        test_cases = [
            ("Build a web dashboard", "web"),
            ("Create a mobile app feature", "mobile"),
            ("Develop a desktop application", "desktop")
        ]
        
        for query, expected_platform in test_cases:
            response = client.post(
                "/natural-query",
                json={"query": query}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            if "platform" in data["entities"]:
                assert data["entities"]["platform"] == expected_platform
                
    def test_workflow_steps_logged(self, client_with_mocked_logger):
        """Test that workflow steps are logged."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan authentication for mobile"}
        )
        
        assert response.status_code == 200
        
        # Verify workflow steps were logged
        assert mock_logger.log_workflow_step.call_count >= 2
        
        # Check for specific steps
        step_calls = [call[1] for call in mock_logger.log_workflow_step.call_args_list]
        step_names = [call['step_name'] for call in step_calls]
        
        assert "query_preprocessing" in step_names
        assert "intent_extraction" in step_names
        
    def test_confidence_scoring(self, client_with_mocked_logger):
        """Test that confidence scores are reasonable."""
        client, mock_logger = client_with_mocked_logger
        
        # High confidence query
        response = client.post(
            "/natural-query",
            json={"query": "Plan a new authentication feature"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["confidence"] >= 0.70  # Minimum threshold
        
    def test_original_query_preserved(self, client_with_mocked_logger):
        """Test that original query is preserved in interpreted_intent."""
        client, mock_logger = client_with_mocked_logger
        
        original_query = "I need to plan a payment system for my web app"
        
        response = client.post(
            "/natural-query",
            json={"query": original_query}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["interpreted_intent"]["original_query"] == original_query
        
    def test_feature_specific_fields_for_planning(self, client_with_mocked_logger):
        """Test that feature-specific fields are added for planning queries."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan a payment feature"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        intent = data["interpreted_intent"]
        assert intent["type"] == "feature_planning"
        assert "feature_type" in intent
        assert "platform" in intent
        assert intent["action"] == "plan"


class TestNaturalQueryErrorHandling:
    """Test error handling in /natural-query endpoint."""
    
    def test_none_query(self, client_with_mocked_logger):
        """Test handling of None query."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={"query": None}
        )
        
        # FastAPI validation should catch this
        assert response.status_code in [400, 422]
        
    def test_whitespace_only_query(self, client_with_mocked_logger):
        """Test handling of whitespace-only query."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={"query": "   "}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "workflow_id" in data["detail"]
        
    def test_logging_failure_doesnt_break_endpoint(self, client_with_mocked_logger):
        """Test that logging failures don't break the endpoint."""
        client, mock_logger = client_with_mocked_logger
        
        # Make logging fail
        mock_logger.log_workflow_start.side_effect = Exception("Logging failed")
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan authentication"}
        )
        
        # Should still return 200 (fail_silently=True)
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data


class TestNaturalQueryIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_workflow_lifecycle(self, client_with_mocked_logger):
        """Test complete workflow from start to finish."""
        client, mock_logger = client_with_mocked_logger
        
        response = client.post(
            "/natural-query",
            json={
                "query": "Plan a new authentication system for our mobile app with a team of 5",
                "user_id": "test-user"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        assert "workflow_id" in data
        assert "interpreted_intent" in data
        assert "entities" in data
        assert "confidence" in data
        assert "processing_time_ms" in data
        assert "next_step" in data
        assert "logged" in data
        assert "timestamp" in data
        
        # Verify intent
        assert data["interpreted_intent"]["type"] == "feature_planning"
        
        # Verify entities
        assert data["entities"]["feature_type"] == "authentication"
        assert data["entities"]["platform"] == "mobile"
        assert data["entities"]["team_size"] == 5
        
        # Verify logging lifecycle
        mock_logger.log_workflow_start.assert_called_once()
        assert mock_logger.log_workflow_step.call_count >= 2
        mock_logger.log_workflow_complete.assert_called_once()
        
        # Verify success flag in completion
        complete_call = mock_logger.log_workflow_complete.call_args
        assert complete_call[1]["success"] is True

