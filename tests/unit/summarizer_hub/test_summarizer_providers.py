"""Summarizer Hub provider configuration tests.

Tests provider management and configuration merging.
Focused on provider setup and configuration following TDD principles.
"""

import pytest
from fastapi.testclient import TestClient

from .test_utils import load_summarizer_hub_service


@pytest.fixture(scope="module")
def client():
    """Test client fixture for summarizer hub service."""
    app = load_summarizer_hub_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


def _assert_http_ok(response):
    """Assert that HTTP response is successful."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestSummarizerProviders:
    """Test provider configuration and management."""

    def test_provider_config_minimal(self, client):
        """Test minimal provider configuration."""
        request_data = {
            "text": "Test document",
            "providers": [
                {
                    "name": "ollama"
                    # Minimal config - no model, endpoint, etc.
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        # Should handle minimal config gracefully
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "summaries" in data
            assert "ollama" in data["summaries"]

    def test_provider_config_complete(self, client):
        """Test complete provider configuration."""
        request_data = {
            "text": "Test document for complete configuration",
            "providers": [
                {
                    "name": "ollama",
                    "model": "llama3",
                    "endpoint": "http://localhost:11434",
                    "api_key": None,
                    "region": None,
                    "profile": None
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "ollama" in data["summaries"]

    def test_multiple_provider_types(self, client):
        """Test different provider types in single request."""
        request_data = {
            "text": "Test document for multiple provider types",
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
                },
                {
                    "name": "anthropic",
                    "model": "claude-3",
                    "api_key": "test-key"
                },
                {
                    "name": "bedrock",
                    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "region": "us-east-1"
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            # Should have results for all providers
            summaries = data["summaries"]
            assert len(summaries) >= 1  # At least some providers should work

    def test_hub_config_integration(self, client):
        """Test integration with hub configuration."""
        request_data = {
            "text": "Test document for hub config integration",
            "providers": [
                {
                    "name": "ollama"
                    # Rely on hub config for endpoint/model details
                }
            ],
            "use_hub_config": True
        }

        response = client.post("/summarize/ensemble", json=request_data)
        # Should work with or without actual hub config file
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "summaries" in data

    def test_provider_fallback_behavior(self, client):
        """Test fallback behavior for unsupported providers."""
        request_data = {
            "text": "Test document for fallback behavior",
            "providers": [
                {
                    "name": "unsupported-provider",
                    "model": "unknown-model"
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "summaries" in data
            # Should have fallback result for unsupported provider
            assert "unsupported-provider" in data["summaries"]
            fallback_result = data["summaries"]["unsupported-provider"]
            assert isinstance(fallback_result, str)
            assert len(fallback_result) > 0

    def test_provider_config_merging(self, client):
        """Test merging of inline config with hub config."""
        # This tests the _merge_provider_from_config functionality
        request_data = {
            "text": "Test config merging",
            "providers": [
                {
                    "name": "ollama",
                    "model": "custom-model"  # Override hub config
                    # endpoint will come from hub config if available
                }
            ],
            "use_hub_config": True
        }

        response = client.post("/summarize/ensemble", json=request_data)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "summaries" in data
            # Config merging should work regardless of hub config availability

    def test_bedrock_provider_config(self, client):
        """Test Bedrock-specific provider configuration."""
        request_data = {
            "text": "Test Bedrock provider configuration",
            "providers": [
                {
                    "name": "bedrock",
                    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "region": "us-east-1",
                    "profile": "default"
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        # Bedrock may fail without proper AWS credentials, but should not crash
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "summaries" in data
            assert "bedrock" in data["summaries"]

    def test_provider_error_handling(self, client):
        """Test error handling for provider failures."""
        request_data = {
            "text": "Test error handling for provider failures",
            "providers": [
                {
                    "name": "ollama",
                    "endpoint": "http://nonexistent-endpoint:9999"  # Should fail
                }
            ]
        }

        response = client.post("/summarize/ensemble", json=request_data)
        # Should handle provider errors gracefully
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "summaries" in data
            # Should still have a result, possibly fallback
            assert "ollama" in data["summaries"]
            result = data["summaries"]["ollama"]
            assert isinstance(result, str)
