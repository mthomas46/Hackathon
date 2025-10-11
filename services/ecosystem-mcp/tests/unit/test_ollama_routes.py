"""
Unit tests for Ollama routes.
"""

import pytest


def test_ollama_request_structure():
    """Test OllamaRequest structure."""
    from src.api.routes.ollama import OllamaRequest
    
    request = OllamaRequest(
        prompt="Tell me a joke",
        model="mistral",
        temperature=0.7,
        max_tokens=100
    )
    
    assert request.prompt == "Tell me a joke"
    assert request.model == "mistral"
    assert request.temperature == 0.7
    assert request.max_tokens == 100


def test_ollama_response_structure():
    """Test OllamaResponse structure."""
    from src.api.routes.ollama import OllamaResponse
    
    response = OllamaResponse(
        response="Here's a joke...",
        model="mistral",
        context_length=4096,
        eval_count=50,
        eval_duration_ms=1000
    )
    
    assert response.response == "Here's a joke..."
    assert response.model == "mistral"
    assert response.eval_count == 50


def test_ollama_status_structure():
    """Test OllamaStatus structure."""
    from src.api.routes.ollama import OllamaStatus
    
    status = OllamaStatus(
        available=True,
        url="http://localhost:11434",
        models=["mistral", "llama3.1"]
    )
    
    assert status.available is True
    assert len(status.models) == 2

