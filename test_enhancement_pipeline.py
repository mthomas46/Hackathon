"""
Comprehensive tests for Enhancement Pipeline (Phase 1+2).

Tests the modular enhancement system end-to-end.
"""

import pytest
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services/ecosystem-mcp/src'))

from services.rag.enhancements import (
    EnhancementConfig,
    EnhancementHooks,
    QueryContext,
    EnhancementPipeline
)


class TestEnhancementConfig:
    """Test EnhancementConfig and presets."""
    
    def test_default_preset(self):
        """Test default preset has correct settings."""
        config = EnhancementConfig.default()
        assert config.enable_hybrid_search is True
        assert config.enable_query_rewriting is True
        assert config.enable_reranking is False  # Off by default
        assert config.enable_context_optimization is True
    
    def test_temporal_preset(self):
        """Test temporal preset optimized for temporal queries."""
        config = EnhancementConfig.temporal_default()
        assert config.enable_hybrid_search is True
        assert config.enable_intent_classification is False  # Temporal explicit
        assert config.enable_difficulty_estimation is False  # Not needed
    
    def test_multipass_preset(self):
        """Test multipass preset optimized for N×M queries."""
        config = EnhancementConfig.multipass_default()
        assert config.enable_hybrid_search is True
        assert config.enable_query_rewriting is False  # Questions specific
        assert config.enable_reranking is False  # Too expensive for N×M
        assert config.context_strategy == "quality_first"
    
    def test_fast_preset(self):
        """Test fast preset for latency-sensitive queries."""
        config = EnhancementConfig.fast()
        assert config.enable_hybrid_search is True  # Only this enabled
        assert config.enable_query_rewriting is False
        assert config.enable_confidence_scoring is False
        assert config.enable_reranking is False
    
    def test_max_quality_preset(self):
        """Test max quality preset enables everything."""
        config = EnhancementConfig.max_quality()
        assert config.enable_hybrid_search is True
        assert config.enable_query_rewriting is True
        assert config.enable_reranking is True  # Expensive but enabled
        assert config.enable_llm_intent is True  # Expensive but enabled
        assert config.quality_threshold == 60.0


class TestQueryContext:
    """Test QueryContext state management."""
    
    def test_creation(self):
        """Test basic creation."""
        context = QueryContext(original_query="test query")
        assert context.original_query == "test query"
        assert context.rewritten_query is None
        assert context.query_variants == []
    
    def test_get_primary_query_original(self):
        """Test returns original when no rewrite."""
        context = QueryContext(original_query="test")
        assert context.get_primary_query() == "test"
    
    def test_get_primary_query_rewritten(self):
        """Test returns rewritten when available."""
        context = QueryContext(
            original_query="test",
            rewritten_query="expanded test"
        )
        assert context.get_primary_query() == "expanded test"
    
    def test_adaptive_parameters(self):
        """Test adaptive parameter retrieval."""
        context = QueryContext(
            original_query="test",
            adaptive_n_results=15,
            adaptive_strategy="quality_first",
            adaptive_enable_reranking=True
        )
        
        assert context.get_n_results(10) == 15
        assert context.get_strategy("balanced") == "quality_first"
        assert context.should_enable_reranking(False) is True


class TestEnhancementHooks:
    """Test EnhancementHooks system."""
    
    def test_no_hooks(self):
        """Test hooks with nothing defined."""
        hooks = EnhancementHooks()
        assert not hooks.has_custom_retrieval()
        assert not hooks.has_custom_generation()
        assert not hooks.has_pre_retrieval_filter()
        assert not hooks.has_post_retrieval_processor()
    
    def test_pre_retrieval_hook(self):
        """Test pre-retrieval hook detection."""
        async def custom_filter(ctx):
            return {"test": "filter"}
        
        hooks = EnhancementHooks(pre_retrieval_filter=custom_filter)
        assert hooks.has_pre_retrieval_filter()
        assert not hooks.has_custom_retrieval()


@pytest.mark.asyncio
class TestEnhancementPipelineIntegration:
    """Integration tests for full pipeline (requires services)."""
    
    async def test_pipeline_initialization(self):
        """Test pipeline can be initialized."""
        try:
            pipeline = EnhancementPipeline()
            assert pipeline is not None
            assert hasattr(pipeline, 'hybrid_search')
            assert hasattr(pipeline, 'query_rewriter')
            assert hasattr(pipeline, 'confidence_scorer')
            print("✅ Pipeline initialization successful")
        except ImportError as e:
            pytest.skip(f"Skipping due to import error: {e}")
    
    async def test_config_conversion(self):
        """Test config to dict conversion."""
        config = EnhancementConfig.default()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "enable_hybrid_search" in config_dict
        assert config_dict["enable_hybrid_search"] is True
        print("✅ Config conversion successful")
    
    async def test_query_context_enrichment(self):
        """Test query context can be enriched."""
        context = QueryContext(original_query="How does Docker work?")
        context.query_variants = ["Docker functionality", "Docker operations"]
        context.adaptive_n_results = 15
        
        assert len(context.query_variants) == 2
        assert context.get_n_results(10) == 15
        print("✅ Query context enrichment successful")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("ENHANCEMENT PIPELINE TEST SUITE")
    print("="*80 + "\n")
    
    # Run tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "not Integration"  # Skip integration tests for now
    ])

