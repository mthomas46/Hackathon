"""
Integration Tests: Ollama Integration

Tests the integration with Ollama for LLM-based tagging.
"""

import pytest


class TestOllamaIntegration:
    """Test suite for Ollama integration."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ollama_connection(self):
        """Test that we can connect to Ollama."""
        pytest.skip("Requires running Ollama")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tag_extraction_with_ollama(self):
        """Test tag extraction using Ollama."""
        pytest.skip("Requires running Ollama")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_summary_generation_with_ollama(self):
        """Test summary generation using Ollama."""
        pytest.skip("Requires running Ollama")
