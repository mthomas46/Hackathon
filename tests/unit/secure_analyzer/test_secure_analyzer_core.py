"""Secure Analyzer Service core functionality tests.

Tests content security analysis, model suggestions, and secure summarization.
Focused on essential secure analyzer operations following TDD principles.
"""
import pytest
from fastapi.testclient import TestClient

from .test_utils import load_secure_analyzer_service, _assert_http_ok


@pytest.fixture(scope="module")
def client():
    """Test client fixture for secure analyzer service."""
    app = load_secure_analyzer_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestSecureAnalyzerCore:
    """Test core secure analyzer functionality."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "secure-analyzer"

    def test_detect_endpoint_basic(self, client):
        """Test basic content detection."""
        content = "This is normal content with no sensitive information."
        request_data = {"content": content}

        response = client.post("/detect", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert "sensitive" in data
        assert "matches" in data
        assert "topics" in data
        assert data["sensitive"] == False
        assert isinstance(data["matches"], list)
        assert isinstance(data["topics"], list)

    def test_detect_sensitive_content(self, client):
        """Test detection of sensitive content."""
        content = """
        User password: secret123
        API key: sk-1234567890abcdef
        Database connection: postgres://user:pass@localhost/db
        """
        request_data = {"content": content}

        response = client.post("/detect", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert data["sensitive"] == True
        assert len(data["matches"]) > 0
        assert len(data["topics"]) > 0

    def test_detect_pii_content(self, client):
        """Test detection of PII (Personally Identifiable Information)."""
        content = """
        User SSN: 123-45-6789
        Social Security Number: 987-65-4321
        Credit card: 4111-1111-1111-1111
        """
        request_data = {"content": content}

        response = client.post("/detect", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert data["sensitive"] == True
        # Should detect SSN and credit card patterns
        assert len(data["matches"]) >= 2

    def test_detect_with_custom_keywords(self, client):
        """Test detection with custom keywords."""
        content = "This document contains proprietary information and trade secrets."
        keywords = ["proprietary", "trade secrets", "confidential"]
        request_data = {
            "content": content,
            "keywords": keywords
        }

        response = client.post("/detect", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert data["sensitive"] == True
        assert len(data["matches"]) > 0

        # Should include custom keyword matches
        matches_text = " ".join(data["matches"]).lower()
        assert any(kw.lower() in matches_text for kw in keywords)

    def test_detect_empty_content(self, client):
        """Test detection with empty content."""
        request_data = {"content": ""}

        response = client.post("/detect", json=request_data)
        assert response.status_code == 422  # Empty content should be rejected

        data = response.json()
        assert "detail" in data  # FastAPI validation error format

    def test_detect_topics_identification(self, client):
        """Test topic identification in content."""
        content = """
        Authentication system using API keys and client credentials.
        Contains user passwords and private keys for secure access.
        """
        request_data = {"content": content}

        response = client.post("/detect", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        # Content should be flagged as sensitive due to patterns or topics
        assert data["sensitive"] == True or len(data["topics"]) > 0

        topics = data["topics"]
        assert isinstance(topics, list)
        # Should identify auth, credentials, secrets topics
        topic_names = [t.lower() for t in topics]
        assert any(t in ["auth", "credentials", "secrets", "pii"] for t in topic_names)

    def test_suggest_endpoint_safe_content(self, client):
        """Test model suggestions for safe content."""
        content = "This is a normal document about machine learning algorithms."
        request_data = {"content": content}

        response = client.post("/suggest", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert "sensitive" in data
        assert "allowed_models" in data
        assert "suggestion" in data

        assert data["sensitive"] == False
        assert isinstance(data["allowed_models"], list)
        assert len(data["allowed_models"]) > 2  # Should allow multiple providers

    def test_suggest_endpoint_sensitive_content(self, client):
        """Test model suggestions for sensitive content."""
        content = """
        System configuration with API keys:
        - OpenAI API Key: sk-1234567890abcdef
        - Database password: super_secret_2024
        """
        request_data = {"content": content}

        response = client.post("/suggest", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert data["sensitive"] == True
        assert isinstance(data["allowed_models"], list)

        # Should restrict to secure models only
        allowed_models = [m.lower() for m in data["allowed_models"]]
        assert any(m in ["bedrock", "ollama"] for m in allowed_models)

        # Should not include less secure models
        assert "openai" not in allowed_models
        assert "anthropic" not in allowed_models

    def test_suggest_with_custom_keywords(self, client):
        """Test suggestions with custom keywords."""
        content = "Project report with internal company data."
        keywords = ["internal", "company"]
        request_data = {
            "content": content,
            "keywords": keywords
        }

        response = client.post("/suggest", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        # Should be sensitive due to custom keywords matching content
        assert data["sensitive"] == True
        assert "recommend" in data["suggestion"].lower()

    def test_summarize_safe_content(self, client):
        """Test summarization of safe content."""
        content = """
        Machine learning is a subset of artificial intelligence that enables
        computers to learn from data without being explicitly programmed.
        There are various types of machine learning algorithms including
        supervised, unsupervised, and reinforcement learning.
        """
        request_data = {"content": content}

        response = client.post("/summarize", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert "summary" in data
        assert "provider_used" in data
        assert "confidence" in data
        assert data["confidence"] > 0

    def test_summarize_sensitive_content_policy_enforcement(self, client):
        """Test summarization policy enforcement for sensitive content."""
        content = """
        Confidential project details:
        API Key: sk-1234567890abcdef
        Database: postgres://admin:secret123@localhost/confidential_db
        """
        request_data = {
            "content": content,
            "providers": [
                {"name": "openai"},
                {"name": "anthropic"},
                {"name": "grok"}
            ]
        }

        response = client.post("/summarize", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        # Should enforce policy and use secure provider
        provider_used = data["provider_used"].lower()
        assert provider_used in ["bedrock", "ollama"]

    def test_summarize_sensitive_content_policy_override(self, client):
        """Test summarization with policy override."""
        content = """
        Sensitive document with API keys and passwords.
        Key: sk-1234567890abcdef
        Password: mySecretPass123
        """
        request_data = {
            "content": content,
            "providers": [{"name": "openai"}],
            "override_policy": True
        }

        response = client.post("/summarize", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        # With override, should use requested provider
        assert data["provider_used"].lower() == "openai"

    def test_summarize_with_custom_prompt(self, client):
        """Test summarization with custom prompt."""
        content = "This is a technical document about security best practices."
        custom_prompt = "Summarize focusing on security implications and risks."

        request_data = {
            "content": content,
            "prompt": custom_prompt
        }

        response = client.post("/summarize", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert "summary" in data
        # Custom prompt should influence the summary
        assert "security" in data["summary"].lower() or "risk" in data["summary"].lower()

    def test_summarize_multiple_providers(self, client):
        """Test summarization with multiple providers."""
        content = "Complex document requiring analysis from multiple AI models."
        request_data = {
            "content": content,
            "providers": [
                {"name": "ollama", "model": "llama2"},
                {"name": "bedrock", "model": "claude"}
            ]
        }

        response = client.post("/summarize", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert "summary" in data
        assert "provider_used" in data

    def test_detect_large_content(self, client):
        """Test detection with large content."""
        # Generate large content
        large_content = "Normal content " * 1000  # ~15KB of content
        request_data = {"content": large_content}

        response = client.post("/detect", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert "sensitive" in data
        assert "matches" in data
        # Large content should still be processed
        assert isinstance(data["matches"], list)

    def test_detect_max_matches_limit(self, client):
        """Test that matches are limited to prevent excessive output."""
        # Content with many sensitive items
        content = "password: secret1\npassword: secret2\n" * 200  # 400 passwords
        request_data = {"content": content}

        response = client.post("/detect", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert data["sensitive"] == True
        # Should limit matches to prevent huge responses
        assert len(data["matches"]) <= 100

    def test_suggest_multiple_keywords(self, client):
        """Test suggestions with multiple custom keywords."""
        content = "Document with multiple sensitive categories."
        keywords = [
            "sensitive", "confidential", "proprietary",
            "internal", "restricted", "classified"
        ]
        request_data = {
            "content": content,
            "keywords": keywords
        }

        response = client.post("/suggest", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert data["sensitive"] == True
        assert isinstance(data["allowed_models"], list)

    def test_summarize_empty_providers_list(self, client):
        """Test summarization with empty providers list."""
        content = "Normal document content."
        request_data = {
            "content": content,
            "providers": []
        }

        response = client.post("/summarize", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert "summary" in data
        assert "provider_used" in data

    def test_detect_case_insensitive_matching(self, client):
        """Test case-insensitive pattern matching."""
        content = """
        PASSWORD: mySecret123
        Api_Key: sk-abcdef123456
        SECRET: confidential_data
        """
        request_data = {"content": content}

        response = client.post("/detect", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        assert data["sensitive"] == True
        assert len(data["matches"]) > 0

    def test_detect_no_false_positives(self, client):
        """Test that normal technical content doesn't trigger false positives."""
        content = """
        This is a technical document discussing:
        - Password hashing algorithms
        - API key authentication flows
        - Secret management systems
        - Client-side security practices
        """
        request_data = {"content": content}

        response = client.post("/detect", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        # Should not be sensitive as these are technical discussions, not actual secrets
        assert data["sensitive"] == False

    def test_suggest_model_restriction_logic(self, client):
        """Test the logic for model restriction based on content sensitivity."""
        # Test boundary between sensitive and non-sensitive
        test_cases = [
            {
                "content": "Normal user documentation",
                "expected_sensitive": False,
                "expected_provider_count": "many"
            },
            {
                "content": "API key: sk-1234567890abcdef",
                "expected_sensitive": True,
                "expected_provider_count": "few"
            },
            {
                "content": "Password: secret123 and API key: sk-abcdef",
                "expected_sensitive": True,
                "expected_provider_count": "few"
            }
        ]

        for test_case in test_cases:
            request_data = {"content": test_case["content"]}

            response = client.post("/suggest", json=request_data)
            _assert_http_ok(response)

            data = response.json()
            assert data["sensitive"] == test_case["expected_sensitive"]

            if test_case["expected_provider_count"] == "many":
                assert len(data["allowed_models"]) > 2
            elif test_case["expected_provider_count"] == "few":
                assert len(data["allowed_models"]) <= 2

    def test_summarize_provider_filtering(self, client):
        """Test provider filtering in summarization."""
        content = "Document with sensitive API key: sk-1234567890abcdef"

        # Request with mixed providers
        request_data = {
            "content": content,
            "providers": [
                {"name": "openai"},
                {"name": "bedrock"},
                {"name": "ollama"},
                {"name": "anthropic"}
            ]
        }

        response = client.post("/summarize", json=request_data)
        _assert_http_ok(response)

        data = response.json()
        # Should filter to only secure providers
        provider_used = data["provider_used"].lower()
        assert provider_used in ["bedrock", "ollama"]

    def test_integration_workflow_detect_to_summarize(self, client):
        """Test integrated workflow from detection to summarization."""
        content = """
        Project documentation containing:
        - API Key: sk-1234567890abcdef
        - Database password: db_secret_2024
        - Client configuration details
        """

        # Step 1: Detect
        detect_response = client.post("/detect", json={"content": content})
        _assert_http_ok(detect_response)
        detect_data = detect_response.json()

        # Step 2: Suggest
        suggest_response = client.post("/suggest", json={"content": content})
        _assert_http_ok(suggest_response)
        suggest_data = suggest_response.json()

        # Step 3: Summarize
        summarize_response = client.post("/summarize", json={"content": content})
        _assert_http_ok(summarize_response)
        summarize_data = summarize_response.json()

        # Verify consistency across services
        assert detect_data["sensitive"] == suggest_data["sensitive"]
        # Summarize should have topics_detected field
        assert "topics_detected" in summarize_data

        # All should agree on sensitivity
        if detect_data["sensitive"]:
            assert len(suggest_data["allowed_models"]) <= 2  # Restricted models
            provider_used = summarize_data["provider_used"].lower()
            assert provider_used in ["bedrock", "ollama"]  # Secure provider
