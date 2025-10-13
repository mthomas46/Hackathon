"""
Unit tests for model router.
"""

import pytest
from src.services.model_router import ModelRouter, LLMTask, LLMModel


@pytest.fixture
def router():
    """Create router instance."""
    return ModelRouter()


def test_calculate_complexity_short_simple(router):
    """Test complexity calculation for short simple text."""
    text = "Hello world"
    complexity = router._calculate_complexity(text, LLMTask.SIMPLE_QUERY)
    
    # Should be low complexity
    assert 0.0 <= complexity <= 0.3


def test_calculate_complexity_long_complex(router):
    """Test complexity calculation for long complex text."""
    text = "Write a comprehensive analysis of the architectural patterns " * 50
    complexity = router._calculate_complexity(text, LLMTask.COMPLEX_ANALYSIS)
    
    # Should be high complexity
    assert 0.7 <= complexity <= 1.0


def test_calculate_complexity_code_generation(router):
    """Test complexity for code generation task."""
    text = "Generate a Python class"
    complexity = router._calculate_complexity(text, LLMTask.CODE_GENERATION)
    
    # Code generation should have higher baseline
    assert complexity >= 0.5


def test_select_model_simple(router):
    """Test model selection for simple task."""
    complexity = 0.2
    model = router._select_model_by_complexity(complexity)
    
    # Should prefer free models
    assert model in [LLMModel.OLLAMA, LLMModel.CURSOR_FREE]


def test_select_model_complex(router):
    """Test model selection for complex task."""
    complexity = 0.9
    model = router._select_model_by_complexity(complexity)
    
    # Should prefer powerful models
    assert model in [LLMModel.CLAUDE_SONNET, LLMModel.CLAUDE_OPUS]


def test_model_fallback_order(router):
    """Test fallback order makes sense."""
    fallback = router._get_fallback_model(LLMModel.CLAUDE_OPUS)
    
    # Should fall back to a reasonable alternative
    assert fallback in [LLMModel.CLAUDE_SONNET, LLMModel.CLAUDE_HAIKU]

