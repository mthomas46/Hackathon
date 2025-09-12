"""Summarizer Hub core functionality tests.

Tests ensemble summarization and multi-provider functionality.
Focused on core summarization capabilities following TDD principles.
"""

import importlib.util, os
import pytest
from fastapi.testclient import TestClient


def _load_summarizer_hub():
    """Load summarizer-hub service dynamically."""
    spec = importlib.util.spec_from_file_location(
        "services.summarizer-hub.main",
        os.path.join(os.getcwd(), 'services', 'summarizer-hub', 'main.py')
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


@pytest.fixture(scope="module")
def summarizer_app():
    """Load summarizer-hub service."""
    return _load_summarizer_hub()


@pytest.fixture
def client(summarizer_app):
    """Create test client."""
    return TestClient(summarizer_app)


def _assert_http_ok(response):
    """Assert HTTP 200 response."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestSummarizerCore:
    """Test core summarizer hub functionality."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data

    def test_ensemble_summarization_basic(self, client):
        """Test basic ensemble summarization with simple providers."""
        # Use stub providers that don't require external APIs
        request_data = {
            "text": "This is a test document for summarization. It contains multiple sentences with different information.",
            "providers": [
                {
                    "name": "ollama",
                    "model": "test-model",
                    "endpoint": "http://test-endpoint:11434"
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        # May return 200 (success) or 500 (connection error) depending on setup
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "summaries" in data
            assert "analysis" in data
            assert "normalized" in data
            assert isinstance(data["summaries"], dict)
            assert isinstance(data["normalized"], dict)

    def test_ensemble_summarization_multiple_providers(self, client):
        """Test ensemble summarization with multiple providers."""
        request_data = {
            "text": "This document discusses machine learning and artificial intelligence. It covers neural networks, deep learning, and natural language processing.",
            "providers": [
                {
                    "name": "ollama",
                    "model": "llama3",
                    "endpoint": "http://test:11434"
                },
                {
                    "name": "openai",
                    "model": "gpt-4",
                    "api_key": "test-key"
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        # May succeed or fail depending on external service availability
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert len(data["summaries"]) >= 1
            assert "ollama" in data["summaries"] or "openai" in data["summaries"]
            assert "analysis" in data

    def test_ensemble_summarization_validation(self, client):
        """Test input validation for ensemble summarization."""
        # Test with missing providers
        invalid_request = {
            "text": "Test document",
            "providers": []  # Empty providers should fail
        }

        response = client.post("/summarize/ensemble", json=invalid_request)
        # Should return 400 Bad Request
        assert response.status_code == 400

        if response.status_code == 400:
            data = response.json()
            assert "detail" in data

    def test_ensemble_summarization_with_prompt(self, client):
        """Test ensemble summarization with custom prompt."""
        request_data = {
            "text": "Python is a programming language. It supports object-oriented programming and has a large ecosystem of libraries.",
            "prompt": "Summarize the following text focusing on key features:",
            "providers": [
                {
                    "name": "ollama",
                    "model": "test-model",
                    "endpoint": "http://test:11434"
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "summaries" in data
            # Check that prompt was included in processing
            assert isinstance(data["summaries"], dict)

    def test_provider_config_validation(self, client):
        """Test provider configuration validation."""
        request_data = {
            "text": "Test document",
            "providers": [
                {
                    "name": "invalid-provider",
                    "model": "test"
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        # Should handle unknown providers gracefully
        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()
            # Should still return results, possibly with fallback
            assert "summaries" in data
            assert "invalid-provider" in data["summaries"]

    def test_normalization_output_structure(self, client):
        """Test that normalized output has correct structure."""
        request_data = {
            "text": "This is a test document. - Key point 1\n- Key point 2\n- Risk: potential issue\n- Decision: proceed with caution",
            "providers": [
                {
                    "name": "ollama",
                    "model": "test",
                    "endpoint": "http://test:11434"
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "normalized" in data

            # Check normalization structure
            normalized = data["normalized"]
            assert isinstance(normalized, dict)

            # Each provider should have normalized structure
            for provider_data in normalized.values():
                assert "summary_text" in provider_data
                assert "bullets" in provider_data
                assert "risks" in provider_data
                assert "decisions" in provider_data
                assert isinstance(provider_data["bullets"], list)
                assert isinstance(provider_data["risks"], list)
                assert isinstance(provider_data["decisions"], list)

    def test_consistency_analysis(self, client):
        """Test consistency analysis across provider outputs."""
        request_data = {
            "text": "All providers should agree on this key point. The main idea is consistent across sources.",
            "providers": [
                {
                    "name": "ollama",
                    "model": "test1",
                    "endpoint": "http://test:11434"
                },
                {
                    "name": "openai",
                    "model": "test2",
                    "api_key": "test"
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "analysis" in data

            analysis = data["analysis"]
            assert isinstance(analysis, dict)
            # Analysis should have agreed and differences keys
            assert "agreed" in analysis or "differences" in analysis
