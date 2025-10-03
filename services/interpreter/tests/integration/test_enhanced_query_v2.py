"""
Integration tests for Phase 2 Enhanced Query Processing.
Tests LLM enrichment, complexity classification, and enhanced entity extraction.
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
def mock_llm_client():
    """Mock LLMGatewayClient for testing."""
    client = MagicMock()
    
    async def mock_enrich(query, basic_entities):
        # Simulate LLM enrichment
        enriched = basic_entities.copy()
        if "authentication" in query.lower():
            enriched["complexity"] = "moderate"
            enriched["security_focus"] = True
        if "deadline" in query.lower():
            enriched["deadline"] = "Q4 2025"
        return enriched
    
    client.enrich_entities = mock_enrich
    return client


@pytest.fixture
def client_with_mocks(mock_workflow_logger, mock_llm_client):
    """Create test client with mocked dependencies."""
    with patch('services.interpreter.main.workflow_logger', mock_workflow_logger):
        with patch('services.interpreter.main.llm_client', mock_llm_client):
            from services.interpreter.main import app
            with TestClient(app) as client:
                yield client, mock_workflow_logger, mock_llm_client


class TestPhase2EnhancedQueryProcessing:
    """Test Phase 2 enhanced query processing features."""
    
    def test_simple_query_classification(self, client_with_mocks):
        """Test that simple queries are correctly classified."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan authentication"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "complexity" in data
        assert data["complexity"] == "simple"
        
    def test_moderate_query_classification(self, client_with_mocks):
        """Test that moderate complexity queries are identified."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={
                "query": "Plan a new authentication feature with OAuth2 and JWT for our mobile app"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["complexity"] in ["moderate", "complex"]
        
    def test_complex_query_classification(self, client_with_mocks):
        """Test that complex queries are identified."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={
                "query": "Plan a comprehensive authentication system with OAuth2, JWT, "
                         "multi-factor authentication, and role-based access control for "
                         "both mobile and web platforms, with a deadline of Q4 2025 and "
                         "a team of 5 developers"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["complexity"] == "complex"
        
    def test_llm_enrichment_flag(self, client_with_mocks):
        """Test that LLM enrichment flag is set correctly."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan authentication with deadline Q4"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "llm_enriched" in data
        # Should be True since mock LLM adds fields
        assert data["llm_enriched"] is True
        
    def test_llm_enrichment_adds_fields(self, client_with_mocks):
        """Test that LLM enrichment adds additional fields."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={
                "query": "Plan authentication feature with deadline Q4 2025"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Mock LLM should add complexity and deadline
        assert "complexity" in data
        if "deadline" in data.get("entities", {}):
            assert data["entities"]["deadline"] == "Q4 2025"
            
    def test_confidence_boost_from_complexity(self, client_with_mocks):
        """Test that complexity classification boosts confidence."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={
                "query": "Plan a new authentication system"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Confidence should be reasonably high
        assert data["confidence"] >= 0.85
        
    def test_technical_terms_increase_complexity(self, client_with_mocks):
        """Test that technical terms increase complexity score."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={
                "query": "Design microservice architecture with Kubernetes and Docker"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Multiple technical terms should increase complexity
        assert data["complexity"] in ["moderate", "complex"]
        
    def test_multiple_requirements_increase_complexity(self, client_with_mocks):
        """Test that multiple requirements increase complexity."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={
                "query": "Build authentication and authorization and also payment system"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Multiple "and" connectors should increase complexity
        assert data["complexity"] in ["moderate", "complex"]
        
    def test_constraints_add_to_complexity(self, client_with_mocks):
        """Test that constraints add to complexity score."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={
                "query": "Plan feature with deadline next month and budget of $50k"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Constraints should increase complexity
        assert data["complexity"] in ["moderate", "complex"]


class TestPhase2LoggingEnhancements:
    """Test Phase 2 logging enhancements."""
    
    def test_query_classification_logged(self, client_with_mocks):
        """Test that query classification is logged."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan authentication"}
        )
        
        assert response.status_code == 200
        
        # Check that classification step was logged
        step_calls = [call[1] for call in mock_logger.log_workflow_step.call_args_list]
        step_names = [call.get('step_name') for call in step_calls]
        
        assert "query_classification" in step_names
        
    def test_llm_enrichment_steps_logged(self, client_with_mocks):
        """Test that LLM enrichment steps are logged."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan authentication"}
        )
        
        assert response.status_code == 200
        
        # Check for LLM enrichment logging
        step_calls = [call[1] for call in mock_logger.log_workflow_step.call_args_list]
        step_names = [call.get('step_name') for call in step_calls]
        
        assert "llm_enrichment_start" in step_names
        assert "llm_enrichment_complete" in step_names
        
    def test_basic_vs_enriched_entity_tracking(self, client_with_mocks):
        """Test that basic and enriched entities are tracked separately."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan authentication"}
        )
        
        assert response.status_code == 200
        
        # Check for basic extraction logging
        step_calls = [call[1] for call in mock_logger.log_workflow_step.call_args_list]
        step_names = [call.get('step_name') for call in step_calls]
        
        assert "basic_entity_extraction" in step_names
        assert "intent_extraction_final" in step_names


class TestPhase2ErrorHandling:
    """Test Phase 2 error handling and fallbacks."""
    
    def test_llm_failure_graceful_fallback(self, client_with_mocks):
        """Test that LLM failure falls back to basic entities."""
        client, mock_logger, mock_llm = client_with_mocks
        
        # Make LLM client fail
        async def failing_enrich(query, basic_entities):
            raise Exception("LLM service unavailable")
        
        mock_llm.enrich_entities = failing_enrich
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan authentication"}
        )
        
        # Should still return 200 with basic entities
        assert response.status_code == 200
        data = response.json()
        
        assert "entities" in data
        assert data["llm_enriched"] is False  # Should indicate no enrichment
        
        # Error should be logged
        mock_logger.log_error.assert_called()


class TestPhase2ResponseStructure:
    """Test Phase 2 enhanced response structure."""
    
    def test_response_includes_new_fields(self, client_with_mocks):
        """Test that response includes all new Phase 2 fields."""
        client, mock_logger, mock_llm = client_with_mocks
        
        response = client.post(
            "/natural-query",
            json={"query": "Plan authentication for mobile"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for all Phase 2 fields
        required_fields = [
            "workflow_id",
            "interpreted_intent",
            "entities",
            "confidence",
            "complexity",  # 🆕 Phase 2
            "processing_time_ms",
            "next_step",
            "logged",
            "llm_enriched",  # 🆕 Phase 2
            "timestamp"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            
    def test_complexity_values_valid(self, client_with_mocks):
        """Test that complexity values are valid."""
        client, mock_logger, mock_llm = client_with_mocks
        
        test_queries = [
            "Simple query",
            "Moderate complexity query with some details and requirements",
            "Very complex query with authentication, authorization, microservices, "
            "Kubernetes, Docker, CI/CD pipeline, and multiple deadlines and constraints"
        ]
        
        valid_complexities = ["simple", "moderate", "complex"]
        
        for query in test_queries:
            response = client.post(
                "/natural-query",
                json={"query": query}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["complexity"] in valid_complexities

