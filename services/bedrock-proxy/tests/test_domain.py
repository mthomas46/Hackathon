"""Tests for bedrock proxy domain layer."""

import pytest
from domain.value_objects.model_name import ModelName
from domain.value_objects.request_id import RequestId
from domain.entities.ai_request import AIRequest
from domain.entities.ai_response import AIResponse
from domain.entities.ai_model import AIModel


class TestModelName:
    """Test ModelName value object."""

    def test_valid_model_name(self):
        """Test creating valid model name."""
        model = ModelName("gpt-4")
        assert str(model) == "gpt-4"

    def test_model_name_validation(self):
        """Test model name validation."""
        # Empty string should raise ValueError
        with pytest.raises(ValueError):
            ModelName("")

        # Whitespace-only should raise ValueError
        with pytest.raises(ValueError):
            ModelName("   ")

        # Valid model name should work
        model = ModelName("gpt-4")
        assert str(model) == "gpt-4"


class TestRequestId:
    """Test RequestId value object."""

    def test_request_id_generation(self):
        """Test request ID generation."""
        request_id = RequestId.generate()
        assert isinstance(request_id, RequestId)
        assert len(str(request_id)) > 0

    def test_request_id_from_string(self):
        """Test creating request ID from string."""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        request_id = RequestId(test_uuid)
        assert str(request_id) == test_uuid


class TestAIRequest:
    """Test AIRequest entity."""

    def test_ai_request_creation(self):
        """Test creating AI request."""
        request = AIRequest(
            id=RequestId.generate(),
            model=ModelName("gpt-4"),
            prompt="Test prompt",
            template="summary"
        )
        assert request.prompt == "Test prompt"
        assert request.template == "summary"

    def test_ai_request_validation(self):
        """Test AI request validation."""
        request = AIRequest(
            id=RequestId.generate(),
            model=ModelName("gpt-4"),
            prompt=""
        )
        with pytest.raises(ValueError):
            request.validate()  # Empty prompt should fail


class TestAIResponse:
    """Test AIResponse entity."""

    def test_ai_response_creation(self):
        """Test creating AI response."""
        response = AIResponse(
            request_id=RequestId.generate(),
            content="Test response",
            model_used="gpt-4",
            tokens_used=10
        )
        assert response.content == "Test response"
        assert response.tokens_used == 10


class TestAIModel:
    """Test AIModel entity."""

    def test_ai_model_creation(self):
        """Test creating AI model."""
        model = AIModel(
            name=ModelName("gpt-4"),
            provider="openai",
            max_tokens=8192
        )
        assert model.provider == "openai"
        assert model.max_tokens == 8192
